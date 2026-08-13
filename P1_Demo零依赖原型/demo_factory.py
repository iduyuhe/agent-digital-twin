# -*- coding: utf-8 -*-
"""
工厂级仿真 · 零依赖 Demo（Streamlit 可视化，支持多工厂类型）
==========================================================
复用 factory_sim_core（SimPy 仿真核心）+ 工厂类型库 FACTORY_LIBRARY。
可选择不同性质的工厂（机加工/装备装配/半导体/汽车流水线/电子组装），各自按自身工艺拓扑
跑双场景，并输出"本厂数字孪生建设方案要点"；支持侧栏实时调节各工位节拍与机器数。
对应 GB/T 45873-2025 车间/工厂数字孪生（生产系统仿真·布局物流·产能）。

依赖：pip install streamlit plotly numpy pandas simpy
运行：streamlit run demo_factory.py
"""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import factory_sim_core as fs


st.set_page_config(page_title="工厂级仿真 Demo", layout="wide")
st.title("工厂级数字孪生 · 零依赖仿真 Demo")
st.caption(
    "降依赖路径：SimPy 离散事件仿真（免商业引擎授权、免云）。"
    "可切换不同性质工厂，按各自工艺拓扑跑双场景并产出建设方案。正式版替换为 Plant Simulation / AnyLogic。"
)

# ------------------------------------------------------------
# 顶部：工厂类型选择器（主内容区，醒目可见）
# ------------------------------------------------------------
factory_keys = [k for k, _ in fs.list_factories()]
factory_labels = [l for _, l in fs.list_factories()]
_fmt_map = dict(zip(factory_keys, factory_labels))
_sel_col, _hint_col = st.columns([1, 2])
with _sel_col:
    factory_type = st.selectbox(
        "🔧 选择工厂类型",
        options=factory_keys,
        format_func=lambda k: _fmt_map.get(k, k),
        index=0,
        key="factory_type_top",
    )
with _hint_col:
    st.markdown(
        "<div style='margin-top:26px;color:#6b7280;font-size:13px;'>"
        "切换后整页按该工厂的工艺拓扑、设备配置与瓶颈结构重算，并生成《本厂数字孪生建设方案要点》。"
        "</div>",
        unsafe_allow_html=True,
    )
spec = fs.get_factory_spec(factory_type)

# ------------------------------------------------------------
# 侧栏：场景 + 参数
# ------------------------------------------------------------
st.sidebar.markdown("### 仿真设置")
scene = st.sidebar.radio("选择场景", ["① 新建厂虚拟验证", "② 存量产能优化"])
sim_hours = st.sidebar.slider("仿真时长（小时，演示压缩）", 24, 960, 480, 24)
sim_minutes = sim_hours * 60.0

# ------------------------------------------------------------
# 侧栏：工位参数调节（节拍 / 机器数），实时重算
# ------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("**⚙️ 工位参数调节**")
st.sidebar.caption("拖动滑块即时改变工艺节拍/机器数，仿真随之下方重算")
if st.sidebar.button("恢复默认参数", key="reset_params"):
    for (nm, _, _, _) in spec["stations"]:
        for k in (f"cyc_{factory_type}_{nm}", f"mac_{factory_type}_{nm}"):
            st.session_state.pop(k, None)

override_spec = []
for (nm, m, s, c) in spec["stations"]:
    ky_c = f"cyc_{factory_type}_{nm}"
    ky_m = f"mac_{factory_type}_{nm}"
    cc1, cc2 = st.sidebar.columns(2)
    cyc = cc1.slider(f"{nm}·节拍(分)", 0.1, 10.0, float(m), 0.1, key=ky_c)
    mac = cc2.number_input(f"{nm}·机器", 1, 8, int(c), 1, key=ky_m)
    override_spec.append((nm, cyc, s, mac))

# ------------------------------------------------------------
# 工厂画像
# ------------------------------------------------------------
st.markdown(f"### 🏭 {spec['display']}")
st.write(spec["desc"])
ch1, ch2, ch3 = st.columns(3)
ch1.metric("设计产能", f"{spec['new_plant']['designed_capacity_per_h']:.0f} 件/时")
ch2.metric("工艺工位数", len(spec["stations"]))
ch3.metric("典型瓶颈", fs.simulate_new_plant(factory_type=factory_type,
                                             stations_spec=override_spec)["bottleneck"])

# 工艺拓扑表
flow = " → ".join(n for n, _, _, _ in spec["stations"])
st.info(f"**工艺路线**：{flow}")

# ------------------------------------------------------------
# 场景仿真
# ------------------------------------------------------------
if scene.startswith("①"):
    st.header("① 新建工厂虚拟验证")
    st.write("在厂房/产线动工前，验证布局、产线平衡率、产能可达性。")
    res = fs.simulate_new_plant(factory_type=factory_type,
                                stations_spec=override_spec, sim_minutes=sim_minutes)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("产能(件/时)", res["throughput_per_h"])
    c2.metric("平均节拍(分)", res["avg_cycle_time_min"])
    c3.metric("产线平衡率", f"{res['line_balance_rate'] * 100:.1f}%")
    c4.metric("瓶颈工位", res["bottleneck"])

    names = list(res["station_util"].keys())
    vals = list(res["station_util"].values())
    fig = go.Figure(go.Bar(x=names, y=vals, marker_color="#2563eb",
                           text=[f"{v*100:.1f}%" for v in vals], textposition="outside"))
    fig.update_layout(title="各工位利用率", yaxis_title="利用率", height=360,
                      yaxis_range=[0, 1.1], margin=dict(l=40, r=20, t=40, b=30))
    st.plotly_chart(fig, use_container_width=True)

    if "reachability" in res:
        st.success(f"✅ 设计产能可达性：{res['reachability'] * 100:.1f}%（仿真产能 / 设计产能 {res['designed_capacity_per_h']:.0f} 件/时）")

else:
    st.header("② 存量工厂产能优化")
    st.write("对运行工厂做瓶颈诊断，对瓶颈工位增资后推演产能爬坡与瓶颈转移。")
    add = st.sidebar.slider("瓶颈工位追加机器数", 1, 3, spec["existing_plant"]["add_machines"])
    res = fs.simulate_existing_plant_optimization(factory_type=factory_type,
                                                  stations_spec=override_spec,
                                                  sim_minutes=sim_minutes, add_machines=add)
    b, o = res["baseline"], res["optimized"]
    c1, c2, c3 = st.columns(3)
    c1.metric("现状产能", b["throughput_per_h"])
    c2.metric("优化产能", o["throughput_per_h"])
    c3.metric("产能爬坡", f"{res['throughput_uplift'] * 100:.1f}%")

    fig = go.Figure()
    fig.add_bar(name="现状", x=["产能"], y=[b["throughput_per_h"]], marker_color="#94a3b8")
    fig.add_bar(name=f"优化(+{add}台)", x=["产能"], y=[o["throughput_per_h"]], marker_color="#2563eb")
    fig.update_layout(title="产能对比（件/小时）", barmode="group", height=320)
    st.plotly_chart(fig, use_container_width=True)

    st.warning(
        f"现状瓶颈：{res['bottleneck_station']}（利用率 {b['bottleneck_util']}）｜"
        f"追加 {add} 台机器后瓶颈{'转移' if res['bottleneck_shifted'] else '未转移'} → {res['new_bottleneck']}"
    )

# ------------------------------------------------------------
# 本厂数字孪生建设方案要点
# ------------------------------------------------------------
st.markdown("---")
st.subheader("📋 本厂数字孪生建设方案要点")
c1, c2 = st.columns([1, 1])
with c1:
    st.markdown("**数字孪生建模重点**")
    st.write(spec["dt_focus"])
    st.markdown("**行业痛点 / 优化重点**")
    for p in spec["pain_points"]:
        st.write(f"• {p}")
with c2:
    st.markdown("**仿真验证建议**")
    st.write(spec["recommend"])
    st.markdown("**设备配置（演示拓扑）**")
    df = pd.DataFrame(
        [(n, f"{m:.1f}", c) for (n, m, s, c) in spec["stations"]],
        columns=["工位", "节拍(分)", "机器数"],
    )
    st.dataframe(df, use_container_width=True, hide_index=True)

st.caption("注：本 Demo 数值为概念验证，不构成 GB/T 45873 合规证据；正式合规走 CESI 测评。")
