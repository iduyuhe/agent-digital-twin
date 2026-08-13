# -*- coding: utf-8 -*-
"""
demo_databus_app.py — 零依赖数据底座 · 实时可视化
=================================================
Streamlit 单页：把 DataBusLite(≈EMQX) 的发布/订阅 与 TsStore(≈IoTDB, SQLite) 的
持久化/查询 串成一条可见的实时数据闭环。证明"采集→路由→落库→回查"无 broker、无 JVM、无云也能跑。

运行：streamlit run demo_databus_app.py   （需 pip install streamlit，其余为标准库）
"""

import time
import pandas as pd
import streamlit as st
from demo_databus_sqlite import LivePipeline, DEVICES

st.set_page_config(page_title='数据底座 Demo · SQLite+队列', layout='wide')
st.title('⚡ 实时数据底座 · 零依赖原型')
st.caption('DataBusLite(≈EMQX 消息路由) + TsStore(≈IoTDB 时序库, SQLite) — 无 broker / 无 JVM / 无云')

# 单例实时管线（后台线程持续发布并落库）
if 'pipe' not in st.session_state:
    pipe = LivePipeline(db_path='demo_databus.db')
    pipe.start()
    st.session_state['pipe'] = pipe
pipe = st.session_state['pipe']

# ---- KPI 卡片 ----
total, n_topics = pipe.store.count()
q0 = time.time()
pipe.store.aggregate(DEVICES[0][0], 'temp', agg='avg')
q_ms = (time.time() - q0) * 1000

c1, c2, c3 = st.columns(3)
c1.metric('已落库采样点', total, 'SQLite 持久化')
c2.metric('活跃设备 topic', n_topics, '3 台设备')
c3.metric('聚合查询延迟', f'{q_ms:.2f} ms', '基准<=200ms')

# ---- 实时曲线（从 SQLite 回查，证明数据已落库）----
opts = [f'{name} ({topic})' for topic, name in DEVICES]
sel = st.selectbox('选择设备', opts)
topic = sel.split('(')[1].rstrip(')')
metric = st.selectbox('指标', ['temp', 'vib', 'rpm'])

rows = pipe.store.query_range(topic, metric, limit=120)
if rows:
    df = pd.DataFrame(rows, columns=['ts', 'v'])
    df['t'] = pd.to_datetime(df['ts'], unit='s')
    st.subheader(f'① {sel} · {metric} 实时时序（回查 SQLite）')
    st.line_chart(df.set_index('t')['v'], use_container_width=True)
    last = rows[-1][1]
    avg = pipe.store.aggregate(topic, metric, agg='avg')
    st.write(f'最新值 **{last:.2f}** ｜ 窗口均值 **{avg:.2f}**')
else:
    st.info('采集落库启动中…')

# ---- 落库查询面板 ----
with st.expander('② SQLite 落库查询（验证持久化，对标 IoTDB）'):
    st.write('以下直接从 SQLite 文件 `demo_databus.db` 回查，证明遥测已持久化、可范围查询/聚合。')
    raw = pipe.store.query_range(topic, metric, limit=12)
    if raw:
        rdf = pd.DataFrame(raw, columns=['ts', 'v'])
        rdf['时间'] = pd.to_datetime(rdf['ts'], unit='s').dt.strftime('%H:%M:%S')
        st.dataframe(rdf[['时间', 'v']].rename(columns={'v': metric}),
                     use_container_width=True, hide_index=True)
    st.write(f'全量均值(聚合)：`{pipe.store.aggregate(topic, metric, agg="avg"):.3f}` ｜ '
             f'峰值(MAX)：`{pipe.store.aggregate(topic, metric, agg="max"):.3f}`')

st.divider()
st.caption('替换路线：正式用 EMQX(消息路由) + IoTDB(时序库) 或 OPC UA 直采，替换本原型；'
           '接口契约一致（publish / subscribe / query_range / aggregate），换引擎不换骨架。'
           '本 Demo 数值为概念验证占位，不构成 GB/T 45626 合规性证据。')

# 自动刷新（每 2 秒）
time.sleep(2)
st.rerun()
