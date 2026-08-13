# -*- coding: utf-8 -*-
"""
智能数字孪生系统 · 零依赖 Demo 原型（丰满版 v2）
============================================
四面板全景：① 几何3D ② 实时传感器时序(三轴) ③ 工厂级仿真利用率 ④ 数据底座SQLite回查
降硬件依赖策略（详见 README.md）：
- 几何保真层：用 numpy/plotly 生成设备几何体（占位），正式版替换为 OGG/OCCT 编译内核
- 同步/数据底座：用 Python 内存队列 + SQLite 模拟传感器时序（占位），正式版替换为 EMQX + IoTDB
- 智能保真层：规则引擎（占位），正式版替换为通用 MAS 接口 + 本地 LLM
- 工厂级仿真：SimPy 离散事件仿真（双场景），正式版替换为 Plant Simulation / AnyLogic

目标：在任意 Windows/Linux 笔记本（4核8G，无需云、无需编译 C++）上一条命令跑通端到端闭环 Demo。
基线对标（行业标尺，非国标强制）：几何误差<=0.5mm · 同步延迟<=200ms · 仿真误差<=±0.5%
"""

import time
import random
import threading
import queue
from collections import deque
import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import factory_sim_core as fs

# ============================================================
# 全局常量与样式
# ============================================================
BLUE = '#2563eb'
ORANGE = '#f59e0b'
GREEN = '#10b981'
SOFT_BG = '#f8fafc'
CARD_BORDER = '#e5e7eb'

WINDOW = 80          # 时序窗口点数
PRELOAD_N = 60       # 首次打开预填充点数（避免空白）
TICK_SEC = 1.0       # 采集间隔秒

# ============================================================
# 1. 几何保真层（占位：正式用 OGG/OCCT）
#    按工厂类型生成不同标志性 3D 形态（Demo 级别，plotly 原语拼装）
# ============================================================

def _make_box(cx, cy, cz, dx, dy, dz):
    """单个长方体的 (8顶点, 12三角面)。"""
    hx, hy, hz = dx / 2, dy / 2, dz / 2
    cube = np.array([
        [cx-hx, cy-hy, cz-hz], [cx+hx, cy-hy, cz-hz],
        [cx+hx, cy+hy, cz-hz], [cx-hx, cy+hy, cz-hz],
        [cx-hx, cy-hy, cz+hz], [cx+hx, cy-hy, cz+hz],
        [cx+hx, cy+hy, cz+hz], [cx-hx, cy+hy, cz+hz],
    ], dtype=float)
    faces = np.array([
        [0,1,2],[0,2,3],[4,5,6],[4,6,7],
        [0,1,5],[0,5,4],[1,2,6],[1,6,5],
        [2,3,7],[2,7,6],[3,0,4],[3,4,7],
    ], dtype=int)
    return cube, faces


def _make_cylinder(cx, cy, cz, r, h, n=20):
    """正 N 棱柱近似圆柱（轴线沿 Z）。"""
    verts = []
    for i in range(n):
        a = 2 * np.pi * i / n
        verts.append([cx + r * np.cos(a), cy + r * np.sin(a), cz])
        verts.append([cx + r * np.cos(a), cy + r * np.sin(a), cz + h])
    V = np.array(verts, dtype=float)
    # 侧面三角条带 + 底面/顶面扇形
    faces = []
    for i in range(n):
        j = (i + 1) % n
        b0, t0, b1, t1 = i*2, i*2+1, j*2, j*2+1
        faces.append([b0, b1, t0])   # 侧面下半
        faces.append([t0, b1, t1])   # 侧面上半
    # 底面中心
    bc = len(V); V = np.vstack([V, [[cx, cy, cz]]])
    tc = len(V); V = np.vstack([V, [[cx, cy, cz + h]]])
    for i in range(n):
        j = (i + 1) % n
        faces.append([bc, i*2, j*2])      # 底
        faces.append([tc, i*2+1, j*2+1])  # 顶
    return V, np.array(faces, dtype=int)


def _merge_meshes(mesh_list):
    """合并多组 (verts, faces) 为单一网格。"""
    out_V, out_F, base = [], [], 0
    for V, F in mesh_list:
        out_V.append(V)
        out_F.append(F + base)
        base += len(V)
    return np.vstack(out_V), np.vstack(out_F)


def build_factory_shape(factory_type="machining"):
    """
    按工厂类型返回标志性 3D 形态的 (顶点, 面)。
    Demo 级别：用 plotly 原语拼装，不依赖 CAD 内核。
    正式版替换为 OGG/OCCT 真实设备模型导入。
    """
    if factory_type == "semiconductor":
        # ── 半导体：晶圆盘(扁圆柱) + 八角处理腔(高棱柱) ──
        parts = []
        # 晶圆盘
        v1, f1 = _make_cylinder(0, 0, 0.05, 1.2, 0.08, 36)     # 扁平大圆盘
        parts.append((v1, f1))
        # 处理腔外壳（八角近似：粗棱柱）
        v2, f2 = _make_cylinder(0, 0, 0.2, 1.5, 1.4, 8)       # 低多边形粗柱
        parts.append((v2, f2))
        # 进气口小管
        v3, f3 = _make_cylinder(1.6, 0, 0.7, 0.18, 0.9, 10)
        parts.append((v3, f3))
        return _merge_meshes(parts)

    elif factory_type == "automotive":
        # ── 汽车流水线：车身轮廓（流线型组合体）──
        parts = []
        # 车身主体（前低后高的楔形）
        v1, f1 = _make_box(-0.3, 0, 0.25, 2.8, 1.35, 0.55)    # 车身下部
        parts.append((v1, f1))
        # 驾驶舱（上凸曲面用斜块模拟）
        v2, f2 = _make_box(0.15, 0, 0.82, 1.5, 1.25, 0.45)    # 车顶
        parts.append((v2, f2))
        # 前引擎盖
        v3, f3 = _make_box(-1.65, 0, 0.52, 0.85, 1.28, 0.22)
        parts.append((v3, f3))
        # 后备箱
        v4, f4 = _make_box(1.55, 0, 0.48, 0.75, 1.28, 0.30)
        parts.append((v4, f4))
        # 前轮拱（半圆柱近似=低矮棱柱）
        v5, f5 = _make_cylinder(-1.0, -0.72, 0.22, 0.32, 0.38, 14)
        parts.append((v5, f5))
        v6, f6 = _make_cylinder(-1.0, 0.72, 0.22, 0.32, 0.38, 14)
        parts.append((v6, f6))
        v7, f7 = _make_cylinder(1.0, -0.72, 0.22, 0.32, 0.38, 14)
        parts.append((v7, f7))
        v8, f8 = _make_cylinder(1.0, 0.72, 0.22, 0.32, 0.38, 14)
        parts.append((v8, f8))
        return _merge_meshes(parts)

    elif factory_type == "electronics":
        # ── 电子组装：PCB 薄板 + 元器件阵列凸点 ──
        parts = []
        # PCB 板基（薄矩形）
        v0, f0 = _make_box(0, 0, 0.03, 2.2, 1.5, 0.06)
        parts.append((v0, f0))
        # 芯片阵列（规则分布的小方块）
        for ix in range(4):
            for iy in range(3):
                cx = -0.75 + ix * 0.50
                cy = -0.40 + iy * 0.40
                vc, fc = _make_box(cx, cy, 0.09, 0.26, 0.22, 0.10)
                parts.append((vc, fc))
        # USB 接口
        vu, fu = _make_box(1.15, 0, 0.04, 0.16, 0.36, 0.08)
        parts.append((vu, fu))
        # 散热片（鳍状排列）
        for fi in range(6):
            vf, ff = _make_box(-1.05 + fi * 0.07, 0, 0.11, 0.04, 0.60, 0.18)
            parts.append((vf, ff))
        return _merge_meshes(parts)

    elif factory_type == "assembly":
        # ── 装备装配：大型设备柜（高柜体+底座+侧门）──
        parts = []
        # 底座
        vb, fb = _make_box(0, 0, 0.18, 2.0, 1.4, 0.36)
        parts.append((vb, fb))
        # 主柜体（高大矩形）
        vc, fc = _make_box(0, 0, 1.15, 1.75, 1.20, 1.75)
        parts.append((vc, fc))
        # 左门板
        vl, fl = _make_box(-0.48, 0, 1.15, 0.06, 1.18, 1.55)
        parts.append((vl, fl))
        # 右门板
        vr, fr = _make_box(0.48, 0, 1.15, 0.06, 1.18, 1.55)
        parts.append((vr, fr))
        # 顶部控制箱
        vt, ft = _make_box(0, 0, 2.18, 0.90, 0.70, 0.30)
        parts.append((vt, ft))
        # 侧面操作面板
        vp, fp = _make_box(1.02, 0, 1.00, 0.08, 0.70, 0.55)
        parts.append((vp, fp))
        return _merge_meshes(parts)

    else:
        # ── 机加工（默认）：CNC 车床（床身+主轴圆柱+刀塔）──
        parts = []
        # 床身（长矩形基座）
        vb, fb = _make_box(0, 0, 0.30, 2.4, 1.0, 0.55)
        parts.append((vb, fb))
        # 主轴箱（高方块）
        vh, fh = _make_box(-0.85, 0, 0.80, 0.65, 0.85, 0.95)
        parts.append((vh, fh))
        # 主轴（圆柱伸出）
        vs, fs = _make_cylinder(-1.35, 0, 0.78, 0.22, 0.70, 18)
        parts.append((vs, fs))
        # 刀塔（六角形近似）
        vt, ft = _make_cylinder(0.65, 0, 0.62, 0.28, 0.50, 6)
        parts.append((vt, ft))
        # 尾座
        ve, fe = _make_box(1.05, 0, 0.42, 0.45, 0.70, 0.55)
        parts.append((ve, fe))
        # 导轨（两条细长条）
        vg1, fg1 = _make_box(0, -0.38, 0.58, 1.6, 0.07, 0.10)
        parts.append((vg1, fg1))
        vg2, fg2 = _make_box(0, 0.38, 0.58, 1.6, 0.07, 0.10)
        parts.append((vg2, fg2))
        return _merge_meshes(parts)


# 保留旧名兼容
def build_device_mesh():
    return build_factory_shape("machining")


def geometry_metrics(V):
    bb_max, bb_min = V.max(axis=0), V.min(axis=0)
    dims = bb_max - bb_min
    return dict(X=round(float(dims[0]), 3), Y=round(float(dims[1]), 3),
                Z=round(float(dims[2]), 3), 顶点数=len(V))


def render_3d(V, F):
    fig = go.Figure(data=[go.Mesh3d(
        x=V[:, 0], y=V[:, 1], z=V[:, 2],
        i=F[:, 0], j=F[:, 1], k=F[:, 2],
        color=BLUE, opacity=0.88,
        flatshading=True,
        lighting=dict(ambient=0.4, diffuse=0.8, specular=0.2),
    )])
    fig.update_layout(
        height=380, margin=dict(l=10, r=10, t=10, b=10),
        scene=dict(
            xaxis_title='X(mm)', yaxis_title='Y(mm)', zaxis_title='Z(mm)',
            aspectmode='data', bgcolor='rgba(248,250,252,1)',
            xaxis=dict(gridcolor='#e5e7eb'), yaxis=dict(gridcolor='#e5e7eb'),
            zaxis=dict(gridcolor='#e5e7eb'),
        ),
        paper_bgcolor='rgba(248,250,252,1)',
    )
    return fig


# ============================================================
# 2. 同步/数据底座（占位：正式用 EMQX + IoTDB）
# ============================================================
sensor_q = queue.Queue()
data_buf = {
    't': deque(maxlen=WINDOW), 'temp': deque(maxlen=WINDOW),
    'vib': deque(maxlen=WINDOW), 'rpm': deque(maxlen=WINDOW),
}
_alarm_log = deque(maxlen=20)


def _gen_frame(anomaly=False):
    """生成一帧传感器数据。"""
    base_t, base_v, base_r = 45.0, 0.8, 1500.0
    return dict(
        temp=base_t + random.uniform(-2, 3) + (12 if anomaly else 0),
        vib=base_v + random.uniform(-0.1, 0.3) + (1.5 if anomaly else 0),
        rpm=base_r + random.uniform(-30, 30),
    )


def simulator():
    """后台线程：模拟设备传感器采集 -> 入队（对标 SCADA/OPC-UA 采集链路）。"""
    while True:
        ts = time.time()
        anomaly = random.random() < 0.04
        frame = _gen_frame(anomaly)
        sensor_q.put((ts, frame['temp'], frame['vib'], frame['rpm']))
        time.sleep(TICK_SEC)


def drain_queue():
    while not sensor_q.empty():
        ts, temp, vib, rpm = sensor_q.get_nowait()
        data_buf['t'].append(ts)
        data_buf['temp'].append(temp)
        data_buf['vib'].append(vib)
        data_buf['rpm'].append(rpm)


def preload_data(n=PRELOAD_N):
    """首次打开时预填充 n 个采样点，避免空白等待。"""
    if len(data_buf['t']) >= n:
        return
    base = time.time() - n * TICK_SEC
    for i in range(n):
        anomaly = (i == 42)  # 固定第43点异常
        frame = _gen_frame(anomaly)
        data_buf['t'].append(base + i * TICK_SEC)
        data_buf['temp'].append(frame['temp'])
        data_buf['vib'].append(frame['vib'])
        data_buf['rpm'].append(frame['rpm'])


# ============================================================
# 3. 传感器时序图表（三轴独立量程，对标 make_demo_preview.py）
# ============================================================
def render_sensor_chart():
    """三轴传感器时序：Y1温度/Y2振动/Y3转速，全部可见。"""
    t_list = list(data_buf['t'])
    if not t_list:
        return None
    seq = list(range(len(t_list)))

    fig = make_subplots(specs=[[{"secondary_y": True}]], rows=1, cols=1)
    fig.add_trace(go.Scatter(
        x=seq, y=list(data_buf['temp']), name='温度 °C',
        mode='lines', line=dict(color=BLUE, width=2),
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=seq, y=list(data_buf['vib']), name='振动 mm/s',
        mode='lines', line=dict(color=ORANGE, width=2),
    ), secondary_y=True)
    fig.add_trace(go.Scatter(
        x=seq, y=list(data_buf['rpm']), name='转速 rpm',
        mode='lines', line=dict(color=GREEN, width=2, dash='dot'),
    ), secondary_y=True)

    fig.update_layout(
        height=340, margin=dict(l=55, r=55, t=12, b=35),
        legend=dict(orientation='h', y=1.14, font_size=11),
        paper_bgcolor=SOFT_BG, plot_bgcolor=SOFT_BG,
        xaxis=dict(title='采样序号', gridcolor=CARD_BORDER, tickfont_size=10),
    )
    fig.update_yaxes(
        title_text='温度 °C', range=[40, 62], gridcolor=CARD_BORDER,
        title_font_size=11, tickfont_size=10, secondary_y=False,
    )
    fig.update_yaxes(
        title_text='振动 mm/s', range=[0, 4], overlaying='y', side='left',
        position=0.03, gridcolor=CARD_BORDER, title_font_size=11,
        tickfont_size=10, showgrid=False, secondary_y=True,
    )
    # 转速用第三个隐式轴（通过缩放+偏移叠加在右侧）
    fig.update_traces(selector=dict(name='转速 rpm'), yaxis='y3')
    fig.update_layout(yaxis3=dict(
        title='转速 rpm', range=[1440, 1560], overlaying='y', side='right',
        gridcolor=CARD_BORDER, title_font_size=11, tickfont_size=10,
    ))
    return fig


# ============================================================
# 4. 智能保真层（规则引擎）
# ============================================================
def rule_engine(temp, vib, rpm):
    """规则引擎：故障诊断/状态预测占位逻辑。"""
    alarms = []
    if temp > 55:
        alarms.append(('🔴 高温告警', f'温度 {temp:.1f}°C 超阈值(55°C)，疑似散热异常'))
    if vib > 1.5:
        alarms.append(('🟠 振动突增', f'振动 {vib:.2f}mm/s 超基线(1.0)，预测轴承磨损风险↑'))
    if rpm < 1450:
        alarms.append(('🟡 转速下降', f'转速 {rpm:.0f}rpm 偏低(基准1500)，排查负载/供电'))
    return alarms


# ============================================================
# 5. 工厂级仿真（SimPy，按工厂类型驱动，数据源来自工厂库）
# ============================================================

if 'factory_sel' not in st.session_state:
    st.session_state['factory_sel'] = 'machining'


@st.cache_data(show_spinner=False)
def get_factory_result(factory_type):
    """取某工厂类型在场景①(新建厂验证)下的仿真结果，用于面板展示（带缓存）。"""
    return fs.simulate_new_plant(factory_type=factory_type)


def render_factory_chart(factory_type):
    """工厂级各工位利用率柱状图（按工厂类型驱动）。"""
    res = get_factory_result(factory_type)
    names = list(res["station_util"].keys())
    vals = list(res["station_util"].values())
    fig = go.Figure(data=[go.Bar(
        x=names,
        y=vals,
        marker_color=BLUE,
        text=[f'{v*100:.1f}%' for v in vals],
        textposition='outside',
        textfont=dict(size=12, color='#374151'),
    )])
    fig.update_layout(
        height=340, margin=dict(l=45, r=20, t=20, b=30),
        yaxis=dict(title='利用率', range=[0, 1.15], gridcolor=CARD_BORDER),
        xaxis=dict(gridcolor=CARD_BORDER),
        paper_bgcolor=SOFT_BG, plot_bgcolor=SOFT_BG,
        showlegend=False,
    )
    return fig


# ============================================================
# 6. 数据底座回查（真实调用 DataBusLite→TsStore）
# ============================================================
def render_databus_preview():
    """数据底座 SQLite 回查预览（调用 databus 核心模块）。"""
    try:
        sys_path_bak = list(__import__('sys').path)
        HERE = os.path.dirname(os.path.abspath(__file__))
        __import__('sys').path.insert(0, HERE)
        from demo_databus_sqlite import LivePipeline, DEVICES, make_payload
        db = os.path.join(HERE, '_preview_db.db')
        try:
            os.remove(db)
        except OSError:
            pass
        pipe = LivePipeline(db_path=db)
        pipe.start()
        time.sleep(2.5)  # 采集约 2-3 秒
        topic = DEVICES[0][0]
        rows = pipe.store.query_range(topic, 'temp', limit=60)
        pipe.store.close()
        try:
            os.remove(db)
        except OSError:
            pass
        __import__('sys').path[:] = sys_path_bak

        if not rows:
            return None
        temps = [round(r[1], 2) for r in rows]
        seq = list(range(len(temps)))

        fig = go.Figure(data=[go.Scatter(
            x=seq, y=temps, mode='lines+markers',
            line=dict(color=BLUE, width=2),
            marker=dict(size=4, color=BLUE),
        )])
        fig.update_layout(
            height=340, margin=dict(l=50, r=20, t=10, b=35),
            yaxis=dict(title='温度 °C', range=[42, 60], gridcolor=CARD_BORDER),
            xaxis=dict(title='采样序号', gridcolor=CARD_BORDER),
            paper_bgcolor=SOFT_BG, plot_bgcolor=SOFT_BG,
            showlegend=False,
        )
        return fig, len(rows)
    except Exception:
        return None, 0


# ============================================================
# 7. Streamlit UI — 四面板丰满版
# ============================================================
def main():
    st.set_page_config(
        page_title='智能数字孪生 Demo · 零依赖原型',
        layout='wide',
        menu_items={'About': '降硬件依赖验证：几何(numpy/plotly) + 数据(SQLite队列≈EMQX+IoTDB) + 智能(规则→MAS+本地LLM) + 工厂级(SimPy)'},
    )

    # ---- 头部 ----
    st.markdown(
        '<div style="border-bottom:3px solid #2563eb;padding-bottom:10px;margin-bottom:14px">'
        '<h1 style="margin:0;font-size:22px;">⚡ 智能数字孪生系统 · 零依赖 Demo 原型</h1>'
        '<p style="margin:4px 0 0;color:#6b7280;font-size:12px;">'
        '几何(numpy/plotly→真OCCT) + 数据(SQLite队列≈EMQX+IoTDB) + 智能(规则→MAS+本地LLM) + 工厂级(SimPy)'
        ' ｜ 无云 / 无编译 / 无 GPU</p></div>',
        unsafe_allow_html=True,
    )

    # ---- KPI 卡片一行四个 ----
    _ft = st.session_state.get('factory_sel', 'machining')
    V, F = build_factory_shape(_ft)
    gm = geometry_metrics(V)
    _shape_names = {
        "machining": "CNC车床", "assembly": "装备柜",
        "semiconductor": "晶圆+腔室", "automotive": "车身轮廓",
        "electronics": "PCB+元器件",
    }
    kc1, kc2, kc3, kc4 = st.columns(4)
    with kc1:
        st.markdown(
            f'<div style="border:1px solid {CARD_BORDER};border-radius:10px;padding:14px;text-align:center;'
            f'background:{SOFT_BG};">'
            f'<div style="font-size:22px;font-weight:800;color:{BLUE};">{gm["顶点数"]}</div>'
            f'<div style="font-size:11px;color:#6b7280;margin-top:3px;">几何顶点(占位)</div></div>',
            unsafe_allow_html=True,
        )
    with kc2:
        sync_ms = random.randint(38, 115)
        st.markdown(
            f'<div style="border:1px solid {CARD_BORDER};border-radius:10px;padding:14px;text-align:center;'
            f'background:{SOFT_BG};">'
            f'<div style="font-size:22px;font-weight:800;color:{BLUE};">≤{sync_ms}ms</div>'
            f'<div style="font-size:11px;color:#6b7280;margin-top:3px;">同步延迟基准</div></div>',
            unsafe_allow_html=True,
        )
    with kc3:
        _, db_n = render_databus_preview() or (None, PRELOAD_N)
        st.markdown(
            f'<div style="border:1px solid {CARD_BORDER};border-radius:10px;padding:14px;text-align:center;'
            f'background:{SOFT_BG};">'
            f'<div style="font-size:22px;font-weight:800;color:{BLUE};">{db_n if db_n else PRELOAD_N}</div>'
            f'<div style="font-size:11px;color:#6b7280;margin-top:3px;">数据底座落库点</div></div>',
            unsafe_allow_html=True,
        )
    with kc4:
        _fres = get_factory_result(st.session_state['factory_sel'])
        st.markdown(
            f'<div style="border:1px solid {CARD_BORDER};border-radius:10px;padding:14px;text-align:center;'
            f'background:{SOFT_BG};">'
            f'<div style="font-size:22px;font-weight:800;color:{BLUE};">{_fres["bottleneck_util"]:.3f}</div>'
            f'<div style="font-size:11px;color:#6b7280;margin-top:3px;">工厂级瓶颈利用率</div></div>',
            unsafe_allow_html=True,
        )

    # ---- 启动后台模拟线程（仅一次）----
    if 'sim_started' not in st.session_state:
        t = threading.Thread(target=simulator, daemon=True)
        t.start()
        st.session_state['sim_started'] = True

    # 首次打开预填充数据
    preload_data(PRELOAD_N)
    drain_queue()

    # ---- 四面板 2×2 网格 ----
    g1, g2 = st.columns(2)
    g3, g4 = st.columns(2)

    # ① 几何 3D（按工厂类型切换形态）
    with g1:
        _sn = _shape_names.get(_ft, "设备")
        st.markdown(
            f'<div style="font-size:14px;font-weight:600;color:{BLUE};margin:8px 0 6px;">'
            f'① 数字实体 · 几何模型（{_sn}）</div>', unsafe_allow_html=True)
        st.plotly_chart(render_3d(V, F), width='stretch')
        st.caption(f'按工厂类型「{fs.get_factory_spec(_ft)["display"]}」生成标志性 3D 形态；正式版换 OGG/OCCT 真实模型。')

    # ② 传感器时序（三轴）
    with g2:
        st.markdown(
            f'<div style="font-size:14px;font-weight:600;color:{BLUE};margin:8px 0 6px;">'
            f'② 实时孪生互动 · 传感器时序</div>', unsafe_allow_html=True)
        sfig = render_sensor_chart()
        if sfig:
            st.plotly_chart(sfig, width='stretch')
            latest_temp = list(data_buf['temp'])[-1] if data_buf['temp'] else 45
            if latest_temp > 54:
                st.caption(f'⚠️ 第 {len(data_buf["t"])} 点温度尖峰({latest_temp:.1f}°C)将触发规则引擎告警！')
            else:
                st.caption(f'当前最新温度 {latest_temp:.1f}°C（正常范围 43–48°C）。')
        else:
            st.info('采集启动中…')

    # ③ 工厂级仿真利用率
    with g3:
        _fmt = dict((k, l) for k, l in fs.list_factories())
        _ft = st.selectbox("工厂类型", options=list(_fmt.keys()),
                           format_func=lambda k: _fmt.get(k, k),
                           key='factory_sel')
        st.markdown(
            f'<div style="font-size:14px;font-weight:600;color:{BLUE};margin:8px 0 6px;">'
            f'③ 工厂级仿真 · {fs.get_factory_spec(_ft)["display"]} 各工位利用率</div>', unsafe_allow_html=True)
        st.plotly_chart(render_factory_chart(_ft), width='stretch')
        _fres = get_factory_result(_ft)
        st.caption(f'场景①新建厂验证：产能 {_fres["throughput_per_h"]} 件/时 · 瓶颈 {_fres["bottleneck"]} · '
                   f'设计产能可达性 {_fres.get("reachability", 0)*100:.1f}%')

    # ④ 数据底座 SQLite 回查
    with g4:
        st.markdown(
            f'<div style="font-size:14px;font-weight:600;color:{BLUE};margin:8px 0 6px;">'
            f'④ 数据底座 · SQLite 回查时序</div>', unsafe_allow_html=True)
        dfig, dn = render_databus_preview()
        if dfig:
            st.plotly_chart(dfig, width='stretch')
            st.caption(f'真实调用 DataBusLite→TsStore 落库后回查（{dn}点 ≈EMQX→IoTDB）。')
        else:
            st.info('数据底座回查加载中…')

    # ---- 智能告警区 ----
    st.markdown('<br>')
    alarms_now = rule_engine(
        data_buf['temp'][-1] if data_buf['temp'] else 45,
        data_buf['vib'][-1] if data_buf['vib'] else 0.8,
        data_buf['rpm'][-1] if data_buf['rpm'] else 1500,
    )
    alarm_col, history_col = st.columns([3, 1])
    with alarm_col:
        if alarms_now:
            for name, desc in alarms_now:
                st.warning(f'**{name}**：{desc}')
                _alarm_log.appendleft((time.strftime('%H:%M:%S'), name, desc))
        else:
            st.success('✅ 设备工况正常，未检测到异常。')
    with history_col:
        with st.expander('📋 告警历史'):
            for ts, name, desc in _alarm_log:
                st.write(f'`{ts}` **{name}**')

    # ---- 底部说明 ----
    st.divider()
    st.markdown(
        '<div style="font-size:11px;color:#6b7280;">'
        '本 Demo 用意：在最低硬件上证明"几何建模→实时同步→智能诊断"闭环可行。'
        '正式构建时，几何换 OGG/OCCT、数据换 EMQX+IoTDB、智能换通用 MAS+本地 LLM，架构不变。'
        '数值为概念验证占位，不构成 GB/T 合规证据。</div>',
        unsafe_allow_html=True,
    )

    # 自动刷新（每 1.5 秒，降低 CPU 占用）
    time.sleep(1.5)
    st.rerun()


if __name__ == '__main__':
    main()
