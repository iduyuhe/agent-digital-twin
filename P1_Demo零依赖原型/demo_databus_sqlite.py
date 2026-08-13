# -*- coding: utf-8 -*-
"""
demo_databus_sqlite.py — 零依赖实时数据底座原型
=================================================
正式方案数据层 = EMQX(MQTT broker) + IoTDB(时序库)。本原型用纯标准库替身证明其概念闭环：

  · DataBusLite       ≈ EMQX  : 进程内 topic 发布/订阅（支持 +/# 通配），模拟 MQTT 消息路由
  · TsStore           ≈ IoTDB : SQLite 时序存储（建表/写入/范围查询/聚合/最新值），模拟时序库
  · PersistenceBridge : 订阅 '#' 把所有遥测落库，模拟 MQTT→IoTDB 桥接

零依赖：仅用到 Python 标准库（sqlite3 / queue / threading / time / random），
        无需 pip 安装、无需 broker、无需 JVM、无需云、无需编译。

运行方式：
  python demo_databus_sqlite.py          # 命令行：批量落库 + 回查验证（证明持久化/查询可行）
  streamlit run demo_databus_app.py      # 实时可视化（见同目录，需 pip install streamlit）
"""

import os
import time
import random
import sqlite3
import threading

# ============================================================
# 1. 主题匹配（对标 MQTT 的 + / # 通配）
# ============================================================
def _topic_match(filt, topic):
    """EMQX 风格主题过滤：'+' 匹配单级，'#' 匹配剩余多级（须为末级）。"""
    f = filt.split('/')
    t = topic.split('/')
    for i, seg in enumerate(f):
        if seg == '#':
            return True
        if i >= len(t):
            return False
        if seg == '+':
            continue
        if seg != t[i]:
            return False
    return len(f) == len(t)


# ============================================================
# 2. DataBusLite  ≈ EMQX（进程内 MQTT 路由）
# ============================================================
class DataBusLite:
    """轻量发布/订阅总线，模拟 MQTT broker 的消息路由语义。"""

    def __init__(self):
        self._subs = []  # [(topic_filter, callback), ...]
        self._lock = threading.Lock()

    def subscribe(self, topic_filter, callback):
        with self._lock:
            self._subs.append((topic_filter, callback))

    def publish(self, topic, payload):
        """payload: {'ts': float, 'fields': {metric: value, ...}}"""
        with self._lock:
            targets = [(f, cb) for (f, cb) in self._subs if _topic_match(f, topic)]
        for _f, cb in targets:
            try:
                cb(topic, payload)
            except Exception:
                # 订阅者异常不影响总线（对标 broker 的 at-most-once 容错）
                pass


# ============================================================
# 3. TsStore  ≈ IoTDB（SQLite 时序库）
# ============================================================
class TsStore:
    """SQLite 时序存储，模拟 IoTDB 的序列模型与查询能力。"""

    def __init__(self, db_path=':memory:'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._lock = threading.Lock()
        self._init()

    def _init(self):
        with self._lock:
            self.conn.execute(
                """CREATE TABLE IF NOT EXISTS ts_data(
                       id     INTEGER PRIMARY KEY AUTOINCREMENT,
                       topic  TEXT NOT NULL,
                       metric TEXT NOT NULL,
                       ts     REAL  NOT NULL,
                       v      REAL  NOT NULL)""")
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_ts ON ts_data(topic, metric, ts)")
            self.conn.commit()

    def write(self, topic, ts, metric, v):
        with self._lock:
            self.conn.execute(
                "INSERT INTO ts_data(topic, metric, ts, v) VALUES(?,?,?,?)",
                (topic, metric, float(ts), float(v)))
            self.conn.commit()

    def write_payload(self, topic, ts, fields):
        # 单次事务批量写入（一帧遥测的多指标），避免逐条 commit 拖慢批量注入
        if not fields:
            return
        with self._lock:
            self.conn.executemany(
                "INSERT INTO ts_data(topic, metric, ts, v) VALUES(?,?,?,?)",
                [(topic, m, float(ts), float(v)) for m, v in fields.items()])
            self.conn.commit()

    def query_range(self, topic, metric, start=None, end=None, limit=1000):
        sql = "SELECT ts, v FROM ts_data WHERE topic=? AND metric=?"
        args = [topic, metric]
        if start is not None:
            sql += " AND ts>=?"; args.append(start)
        if end is not None:
            sql += " AND ts<=?"; args.append(end)
        sql += " ORDER BY ts ASC LIMIT ?"; args.append(limit)
        with self._lock:
            return self.conn.execute(sql, args).fetchall()

    def latest(self, topic, metric):
        with self._lock:
            return self.conn.execute(
                "SELECT ts, v FROM ts_data WHERE topic=? AND metric=? "
                "ORDER BY ts DESC LIMIT 1", (topic, metric)).fetchone()

    def aggregate(self, topic, metric, start=None, end=None, agg='avg'):
        fun = {'avg': 'AVG', 'min': 'MIN', 'max': 'MAX',
               'sum': 'SUM', 'count': 'COUNT'}.get(agg, 'AVG')
        sql = f"SELECT {fun}(v) FROM ts_data WHERE topic=? AND metric=?"
        args = [topic, metric]
        if start is not None:
            sql += " AND ts>=?"; args.append(start)
        if end is not None:
            sql += " AND ts<=?"; args.append(end)
        with self._lock:
            row = self.conn.execute(sql, args).fetchone()
        return row[0] if row else None

    def count(self):
        with self._lock:
            return self.conn.execute(
                "SELECT COUNT(*), COUNT(DISTINCT topic) FROM ts_data").fetchone()

    def close(self):
        self.conn.close()


# ============================================================
# 4. 持久化桥接  MQTT→IoTDB（订阅 '#' 全量落库）
# ============================================================
class PersistenceBridge:
    def __init__(self, store):
        self.store = store

    def on_message(self, topic, payload):
        self.store.write_payload(topic, payload.get('ts'), payload.get('fields', {}))


# ============================================================
# 5. 数据源适配层（解耦"数据从哪来"与"总线/落库"）
# ============================================================
# 设计意图：当前系统未安装 MES/SCADA，先用 SimulatedSource 跑通闭环；
# 待真系统就绪，仅需把 LivePipeline/Pipeline 的数据源换成 CsvFileSource 或
# MesRestSource 即可，下游（总线路由→落库→回查）完全不感知数据来源。
DEVICES = [
    ('factory/line1/dev01', 'CNC-01'),
    ('factory/line1/dev02', 'CNC-02'),
    ('factory/line2/dev01', 'ASM-01'),
]


def make_payload(topic):
    """生成一台设备的多指标遥测（含偶发异常，用于后续智能层告警）。"""
    anomaly = random.random() < 0.05
    return {
        'temp': 45.0 + random.uniform(-2, 3) + (12 if anomaly else 0),
        'vib': 0.8 + random.uniform(-0.1, 0.3) + (1.5 if anomaly else 0),
        'rpm': 1500.0 + random.uniform(-30, 30),
    }


class DataSource:
    """数据源适配层基类：把外部数据源（模拟器 / CSV 文件 / MES REST / OPC-UA）
    统一成 devices() + sample(topic) 两个接口。"""

    def devices(self):
        """返回 [(topic, name), ...]"""
        raise NotImplementedError

    def sample(self, topic):
        """返回一台设备在"当前采样时刻"的帧 {'ts':float,'fields':{...}} 或 None。"""
        raise NotImplementedError


class SimulatedSource(DataSource):
    """默认数据源：进程内随机模拟遥测（对标 SCADA/OPC-UA 采集占位）。"""

    def __init__(self, devices=None):
        self._devices = devices if devices is not None else DEVICES

    def devices(self):
        return self._devices

    def sample(self, topic):
        return {'ts': time.time(), 'fields': make_payload(topic)}


class CsvFileSource(DataSource):
    """CSV 文件数据源（可运行）：直接用 MES/SCADA 导出的 CSV 验证接缝，零外部依赖。
    长格式每行一个指标：ts,topic,temp,vib,rpm（缺失列自动跳过）。
    按 ts 顺序分组回放；读完可按 loop 循环或停止。
    用法示例：
        src = CsvFileSource('mes_export.csv')
        pipe = LivePipeline(source=src)        # 实时管线直接喂真实导出
    """

    def __init__(self, path, devices=None, loop=True):
        self.path = path
        self.loop = loop
        self._by_topic = {}
        self._pos = {}
        self._devices = devices if devices is not None else self._infer_devices(path)
        self._load(path)

    @staticmethod
    def _infer_devices(path):
        import csv
        seen = []
        with open(path, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                t = row.get('topic')
                if t and t not in seen:
                    seen.append(t)
        return [(t, t.split('/')[-1]) for t in seen]

    def _load(self, path):
        import csv
        with open(path, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                topic = row.get('topic')
                if not topic:
                    continue
                fields = {}
                for m in ('temp', 'vib', 'rpm'):
                    v = row.get(m)
                    if v not in (None, ''):
                        try:
                            fields[m] = float(v)
                        except ValueError:
                            pass
                ts = float(row.get('ts', time.time()))
                self._by_topic.setdefault(topic, []).append((ts, fields))
        for t, lst in self._by_topic.items():
            lst.sort(key=lambda x: x[0])
            self._pos[t] = 0

    def devices(self):
        return self._devices

    def sample(self, topic):
        lst = self._by_topic.get(topic)
        if not lst:
            return None
        i = self._pos.get(topic, 0)
        if i >= len(lst):
            if self.loop:
                self._pos[topic] = 0
                i = 0
            else:
                return None
        frame = lst[i]
        self._pos[topic] = i + 1
        return {'ts': frame[0], 'fields': frame[1]}


class MesRestSource(DataSource):
    """MES/SCADA REST 数据源占位（正式环境启用）。
    待 MES/SCADA 安装并开通接口后，填 endpoint+token，实现拉取遥测。
    当前未配置时构造函数即报错，避免误接空转。"""

    def __init__(self, endpoint=None, token=None, devices=None):
        if not endpoint:
            raise ValueError('MesRestSource 需配置 endpoint；未就绪请沿用 SimulatedSource。')
        self.endpoint = endpoint
        self.token = token
        self._devices = devices if devices is not None else []

    def devices(self):
        return self._devices

    def sample(self, topic):
        # TODO(P1→正式): 用 requests 拉取 topic 对应遥测，例如：
        #   import requests
        #   r = requests.get(self.endpoint + '/telemetry',
        #                    params={'topic': topic},
        #                    headers={'Authorization': f'Bearer {self.token}'},
        #                    timeout=2)
        #   return {'ts': time.time(), 'fields': r.json()}
        raise NotImplementedError('MES REST 数据源待实现（requests 拉取逻辑）')


def simulate_batch(bus, source=None, n_points=200, step=0.1):
    """同步批量注入（CLI 演示用）：n_points 个采样时刻 × 全部设备。
    source 缺省为 SimulatedSource；可传入 CsvFileSource 等做真实导出回放。"""
    src = source if source is not None else SimulatedSource()
    base = time.time()
    for i in range(n_points):
        ts = base + i * step
        for topic, _ in src.devices():
            frame = src.sample(topic)
            if frame:
                bus.publish(topic, {'ts': ts, 'fields': frame['fields']})


# ============================================================
# 6. 实时管线（Streamlit 用：后台线程持续发布）
# ============================================================
class LivePipeline:
    def __init__(self, db_path='demo_databus.db', source=None):
        self.store = TsStore(db_path)
        self.bus = DataBusLite()
        self.bridge = PersistenceBridge(self.store)
        self.bus.subscribe('#', self.bridge.on_message)
        self.source = source if source is not None else SimulatedSource()
        self._running = False

    def start(self):
        if self._running:
            return
        self._running = True
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def _loop(self):
        while True:
            for topic, _ in self.source.devices():
                frame = self.source.sample(topic)
                if frame:
                    self.bus.publish(topic, frame)
            time.sleep(1.0)


# ============================================================
# 7. CLI 演示：落库 + 回查，证明持久化/查询闭环
# ============================================================
def run_demo():
    here = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(here, 'demo_databus.db')
    store = TsStore(db_path)
    bus = DataBusLite()
    bridge = PersistenceBridge(store)
    bus.subscribe('#', bridge.on_message)  # 全量落库桥接

    print('=' * 64)
    print(' 零依赖实时数据底座原型 · 落库 + 回查验证')
    print(' DataBusLite(≈EMQX)  →  TsStore(≈IoTDB, SQLite)')
    print('=' * 64)

    t0 = time.time()
    simulate_batch(bus, n_points=200)
    ingest_ms = (time.time() - t0) * 1000

    total, n_topics = store.count()
    print(f'\n[落库] 采样点={total}  设备topic={n_topics}  注入耗时≈{ingest_ms:.1f}ms')

    print('\n[回查] 各设备 / 指标 最新值 与 均值：')
    print(f'  {"设备":<8} {"指标":<6} {"最新值":>10} {"均值":>10}')
    print('  ' + '-' * 40)
    for topic, name in DEVICES:
        for metric in ('temp', 'vib', 'rpm'):
            last = store.latest(topic, metric)
            avg = store.aggregate(topic, metric, agg='avg')
            lv = f'{last[1]:.2f}' if last else '—'
            av = f'{avg:.2f}' if avg is not None else '—'
            print(f'  {name:<8} {metric:<6} {lv:>10} {av:>10}')

    # 范围查询示例：最后一个采样时刻前 5 秒窗口
    now = time.time()
    rows = store.query_range(DEVICES[0][0], 'temp', start=now - 5, limit=50)
    print(f'\n[范围查询] {DEVICES[0][1]} 温度 近5秒窗口点数={len(rows)} '
          f'(对标 IoTDB 时序检索)')

    q0 = time.time()
    store.aggregate(DEVICES[0][0], 'temp', agg='avg')
    print(f'[聚合查询] 单次均值聚合耗时≈{(time.time()-q0)*1000:.2f}ms')

    print('\n[结论] 数据已持久化至 SQLite 文件，支持发布/订阅路由 + 时序范围查询/聚合，')
    print('        概念上等价于 "EMQX 消息路由 + IoTDB 时序库" 的最小闭环。')
    print('        正式交付时按相同接口契约（publish/subscribe/query_range/aggregate）')
    print('        换引擎不换骨架：EMQX+IoTDB 或 OPC UA 直采。')

    store.close()
    return dict(total=total, topics=n_topics, ingest_ms=ingest_ms)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'gen-sample':
        # 生成一份 MES/SCADA 导出样例 CSV，用于离线验证数据源接缝
        out = sys.argv[2] if len(sys.argv) > 2 else 'mes_export_sample.csv'
        import csv
        base = time.time()
        with open(out, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['ts', 'topic', 'temp', 'vib', 'rpm'])
            for i in range(120):
                ts = base + i * 0.5
                for topic, _ in DEVICES:
                    p = make_payload(topic)
                    w.writerow([f'{ts:.3f}', topic, f"{p['temp']:.2f}",
                                f"{p['vib']:.2f}", f"{p['rpm']:.1f}"])
        print(f'样例 CSV 已生成：{out}（120 采样×{len(DEVICES)}设备）')
        print(f'   验证接缝：python demo_databus_sqlite.py replay {out}')
    elif len(sys.argv) > 1 and sys.argv[1] == 'replay':
        # 用真实 CSV 文件回放，证明"换数据源不换骨架"
        csv_path = sys.argv[2] if len(sys.argv) > 2 else 'mes_export_sample.csv'
        here = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(here, 'demo_databus_replay.db')
        src = CsvFileSource(csv_path, loop=False)
        store = TsStore(db_path)
        bus = DataBusLite()
        bus.subscribe('#', PersistenceBridge(store).on_message)
        # 逐设备顺序回放 CSV 全部帧（CSV 已含真实 ts，不走 simulate_batch 合成）
        for topic, _ in src.devices():
            while True:
                fr = src.sample(topic)
                if fr is None:
                    break
                bus.publish(topic, fr)
        total, n_topics = store.count()
        print(f'[CSV回放] 文件={csv_path} 落库点数={total} 设备topic={n_topics}')
        print('  → 与模拟器走完全相同的 总线→落库→回查 路径，证明数据源接缝可用。')
        store.close()
    else:
        run_demo()
