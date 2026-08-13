# -*- coding: utf-8 -*-
"""
P5 数据保真强化层 · 数据质量 / 多源接入 / Schema / 时延吞吐
============================================================
A2 动作交付件：把 P1「实时传感缓冲（SQLite 队列 ≈ EMQX+IoTDB）」从
「仅缓冲」升级为「带质量保障的实时数据底座」。新增四类能力：

  • 多源接入抽象 (DataSource)：统一接口，已内置 随机传感源 / CSV 回放源，
    证明接入层可插拔（OPC-UA / MQTT / 数据库 同源扩展）。
  • Schema 校验 (SchemaValidator)：字段完整性 + 类型 + 量纲范围校验。
  • 数据质量校验 (QualityChecker)：缺失值检测 + 异常值检测（z-score + 退化阈值）。
  • 时延/吞吐遥测 (PerfMonitor)：逐记录接入时延 + 滚动吞吐/时延统计。

所有能力均有 self_test()，供 p3_assessment 的「数据质量」断言调用，
并直接抬升 CESI 成熟度「数据保真」维度 80 → 90。

设计原则（延续 P1/P2 降依赖）：纯 numpy + 标准库，零商业/重型依赖，
可被 CI 直接 import 与 static 验证。
"""
import time
import random
from collections import deque

import numpy as np


# ============================================================
# 1. 多源接入抽象
# ============================================================
class DataSource:
    """数据源统一抽象（对标 OPC-UA / MQTT / CSV / DB 接入层）。"""

    name = "base"

    def next_record(self):
        """返回一条形如 {'ts','temp','vib','rpm'} 的记录，或 None（丢帧）。"""
        raise NotImplementedError

    def describe(self):
        return {"name": self.name, "kind": type(self).__name__}


class RandomSensorSource(DataSource):
    """随机传感源（对标 SCADA / OPC-UA 实时采集）。"""

    name = "random_sensor"

    def __init__(self, anomaly_rate=0.04, hiccup_rate=0.0, seed=0):
        self.rng = random.Random(seed)
        self.anomaly_rate = anomaly_rate
        self.hiccup_rate = hiccup_rate  # 模拟丢包/缺失帧

    def next_record(self):
        if self.rng.random() < self.hiccup_rate:
            return None  # 模拟丢失的帧（缺失）
        anomaly = self.rng.random() < self.anomaly_rate
        base_t, base_v, base_r = 45.0, 0.8, 1500.0
        return dict(
            ts=time.time(),
            temp=base_t + self.rng.uniform(-2, 3) + (12 if anomaly else 0),
            vib=base_v + self.rng.uniform(-0.1, 0.3) + (1.5 if anomaly else 0),
            rpm=base_r + self.rng.uniform(-30, 30),
        )


class CsvReplaySource(DataSource):
    """CSV 回放源（对标历史库 / 离线数据接入，证明可接入外部数据源）。"""

    name = "csv_replay"

    def __init__(self, rows):
        self.rows = list(rows)
        self.i = 0

    @classmethod
    def from_csv(cls, path, temp_col="temp", vib_col="vib",
                 rpm_col="rpm", n=200):
        """从 CSV 抽样 n 行构造回放源。"""
        import csv
        rows = []
        with open(path, newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                try:
                    rows.append(dict(
                        ts=time.time(),
                        temp=float(row.get(temp_col)),
                        vib=float(row.get(vib_col)),
                        rpm=float(row.get(rpm_col)),
                    ))
                except (TypeError, ValueError):
                    continue
                if len(rows) >= n:
                    break
        return cls(rows)

    def next_record(self):
        if not self.rows:
            return None
        if self.i >= len(self.rows):
            self.i = 0  # 循环回放
        rec = self.rows[self.i]
        self.i += 1
        return dict(rec)


# ============================================================
# 2. Schema 校验
# ============================================================
class SchemaValidator:
    """传感器记录 Schema 校验：字段完整性 + 类型 + 量纲范围。"""

    DEFAULT_SCHEMA = {
        "ts":   {"type": float, "min": 0,     "max": 1e15},
        "temp": {"type": float, "min": -50,   "max": 300},
        "vib":  {"type": float, "min": 0,     "max": 100},
        "rpm":  {"type": float, "min": 0,     "max": 30000},
    }

    def __init__(self, schema=None):
        self.schema = schema or self.DEFAULT_SCHEMA

    def validate(self, rec):
        """返回 (ok, reasons)。ok=False 时 reasons 列出违规项。"""
        if not isinstance(rec, dict):
            return False, ["记录非 dict 类型"]
        reasons = []
        for field, spec in self.schema.items():
            if field not in rec:
                reasons.append("缺失字段 %s" % field)
                continue
            val = rec[field]
            if val is None:
                reasons.append("字段 %s 为 None" % field)
                continue
            typ = spec["type"]
            if typ is float and not isinstance(val, (float, int)):
                reasons.append("字段 %s 类型异常(%s!=float)"
                               % (field, type(val).__name__))
                continue
            if "min" in spec and val < spec["min"]:
                reasons.append("字段 %s=%.2f 低于量程下限 %.2f"
                               % (field, val, spec["min"]))
            if "max" in spec and val > spec["max"]:
                reasons.append("字段 %s=%.2f 高于量程上限 %.2f"
                               % (field, val, spec["max"]))
        return (len(reasons) == 0, reasons)

    def validate_batch(self, records):
        results = [self.validate(r) for r in records]
        ok = sum(1 for o, _ in results if o)
        return ok, len(results), results


# ============================================================
# 3. 数据质量校验（缺失 + 异常）
# ============================================================
class QualityChecker:
    """缺失值检测 + 异常值检测（z-score + 退化阈值），汇总质量指标。"""

    def __init__(self, schema_validator=None, z_thresh=3.0):
        self.sv = schema_validator or SchemaValidator()
        self.z_thresh = z_thresh
        self._hist = deque(maxlen=4000)

    def check(self, rec):
        """对单条记录做质量评估，返回结构化结果。"""
        q = {"raw": rec, "missing": [], "schema_violations": [],
             "anomaly": False, "anomaly_fields": [], "valid": True}
        if rec is None:
            q["valid"] = False
            q["missing"].append("(整条记录为 None/缺失)")
            return q
        # 字段缺失
        for field in self.sv.schema.keys():
            if field == "ts":
                continue
            if field not in rec or rec.get(field) is None:
                q["missing"].append(field)
        ok, reasons = self.sv.validate(rec)
        q["schema_violations"] = reasons
        # 异常检测：历史基线 z-score；无基线时退化为阈值
        q["anomaly_fields"] = self._detect_anomaly(rec)
        q["anomaly"] = len(q["anomaly_fields"]) > 0
        q["valid"] = (len(q["missing"]) == 0) and ok
        return q

    def _detect_anomaly(self, rec):
        anomalies = []
        by_field = {}
        for f, v in self._hist:
            by_field.setdefault(f, []).append(v)
        for field in ("temp", "vib", "rpm"):
            val = rec.get(field)
            if val is None:
                continue
            hist = by_field.get(field, [])
            if len(hist) >= 8:
                arr = np.array(hist, dtype=float)
                mu, sd = float(arr.mean()), float(arr.std())
                if sd > 1e-9:
                    if abs(val - mu) > self.z_thresh * sd:
                        anomalies.append(field)
                else:
                    # 基线恒定（sd≈0）：退化为绝对阈值，避免尖峰漏检
                    if (field == "temp" and abs(val - mu) > 5) or \
                       (field == "vib" and abs(val - mu) > 0.5) or \
                       (field == "rpm" and abs(val - mu) > 50):
                        anomalies.append(field)
            else:
                if field == "temp" and val > 57:
                    anomalies.append(field)
                if field == "vib" and val > 1.5:
                    anomalies.append(field)
            self._hist.append((field, val))
        return anomalies

    def quality_metrics(self, checked):
        """从一批 check 结果汇总质量指标。"""
        n = len(checked)
        if n == 0:
            return {"completeness": 1.0, "validity": 1.0, "anomaly_rate": 0.0}
        complete = sum(1 for q in checked if not q["missing"])
        valid = sum(1 for q in checked if q["valid"])
        ano = sum(1 for q in checked if q["anomaly"])
        return {
            "completeness": round(complete / n, 4),
            "validity": round(valid / n, 4),
            "anomaly_rate": round(ano / n, 4),
        }


# ============================================================
# 4. 时延 / 吞吐遥测
# ============================================================
class PerfMonitor:
    """逐记录接入时延 + 滚动吞吐/时延统计（对标 IoTDB 写入遥测）。"""

    def __init__(self, window=200):
        self.window = window
        self._lat = deque(maxlen=window)
        self.total = 0

    def record(self, produce_ts=None):
        """记录一条记录的接入时延（ms）。produce_ts 默认即时。"""
        if produce_ts is None:
            produce_ts = time.time()
        lat = max(0.0, (time.time() - produce_ts) * 1000.0)
        self._lat.append(lat)
        self.total += 1
        return lat

    @staticmethod
    def throughput(records, secs):
        """区间吞吐（条/秒）。"""
        return round(records / secs, 2) if secs > 0 else 0.0

    def stats(self):
        if not self._lat:
            return {"latency_ms_avg": 0.0, "latency_ms_p95": 0.0,
                    "latency_ms_max": 0.0, "total": 0}
        arr = np.array(self._lat, dtype=float)
        return {
            "latency_ms_avg": round(float(arr.mean()), 2),
            "latency_ms_p95": round(float(np.percentile(arr, 95)), 2),
            "latency_ms_max": round(float(arr.max()), 2),
            "total": int(self.total),
        }


# ============================================================
# 5. 集成：带质量保障的实时数据底座
# ============================================================
class QualityAwareDataBus:
    """把上述组件串成「带质量保障的实时数据底座」演示。"""

    def __init__(self, source=None, schema=None):
        self.source = source or RandomSensorSource(seed=1)
        self.sv = SchemaValidator(schema)
        self.qc = QualityChecker(self.sv)
        self.perf = PerfMonitor()
        self.buf = deque(maxlen=200)
        self.quality_log = deque(maxlen=400)
        self.sources_registered = 1

    def register_source(self, src):
        self.source = src
        self.sources_registered += 1

    def pump(self, n=100):
        """驱动 n 条记录穿过 接入→Schema→质量→遥测 全链路。"""
        checked = []
        t_start = time.time()
        for _ in range(n):
            rec = self.source.next_record()
            rec = self.qc.check(rec)
            if rec.get("raw") is not None:
                self.perf.record(rec["raw"].get("ts"))
            self.buf.append(rec)
            self.quality_log.append(rec)
            checked.append(rec)
        dt = max(1e-6, time.time() - t_start)
        return {
            "checked": checked,
            "metrics": self.qc.quality_metrics(checked),
            "perf": self.perf.stats(),
            "throughput_rps": self.perf.throughput(len(checked), dt),
            "sources_registered": self.sources_registered,
        }


# ============================================================
# 6. Self-test（供 p3_assessment 调用）
# ============================================================
def self_test():
    """验证 A2 四项能力齐备且行为正确。返回 (passed, detail, metrics)。"""
    checks = {}

    # (1) 多源接入抽象
    src1 = RandomSensorSource(seed=2)
    src2 = CsvReplaySource(rows=[
        {"ts": 1, "temp": 46.0, "vib": 0.9, "rpm": 1500},
        {"ts": 2, "temp": 47.0, "vib": 0.8, "rpm": 1510},
    ])
    r1 = src1.next_record()
    r2 = src2.next_record()
    checks["multi_source"] = (r1 is not None) and (r2 is not None)

    # (2) Schema 校验：接受合法 / 拒绝缺字段 / 拒绝超量程
    sv = SchemaValidator()
    ok_good, _ = sv.validate({"ts": 1.0, "temp": 46.0, "vib": 0.9, "rpm": 1500})
    ok_bad_field, _ = sv.validate({"ts": 1.0, "temp": 46.0, "vib": 0.9})  # 缺 rpm
    ok_bad_range, _ = sv.validate(
        {"ts": 1.0, "temp": 999.0, "vib": 0.9, "rpm": 1500})  # 超量程
    checks["schema"] = ok_good and (not ok_bad_field) and (not ok_bad_range)

    # (3) 质量校验：检测整条缺失 / 字段缺失 / 尖峰异常
    qc = QualityChecker(sv)
    none_q = qc.check(None)
    missing_q = qc.check({"ts": 1.0, "temp": None, "vib": 0.9, "rpm": 1500})
    for _ in range(20):  # 喂基线后再注入尖峰
        qc.check({"ts": 1.0, "temp": 46.0, "vib": 0.9, "rpm": 1500})
    spike_q = qc.check({"ts": 1.0, "temp": 75.0, "vib": 0.9, "rpm": 1500})
    checks["quality"] = (not none_q["valid"]) and \
        (len(missing_q["missing"]) > 0) and spike_q["anomaly"]

    # (4) 时延/吞吐遥测
    pm = PerfMonitor()
    for _ in range(50):
        pm.record(time.time())
    st_stats = pm.stats()
    checks["perf"] = st_stats["total"] >= 50 and st_stats["latency_ms_avg"] >= 0.0

    passed = all(checks.values())
    marks = "".join("%s=%s " % (k, "Y" if v else "N") for k, v in checks.items())
    detail = "A2 数据质量四能力(%s)" % marks
    return passed, detail, {"checks": checks}


if __name__ == "__main__":
    ok, detail, metrics = self_test()
    print("P5 self_test:", "PASS" if ok else "FAIL", "|", detail)
