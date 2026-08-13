# -*- coding: utf-8 -*-
"""
智能数字孪生系统 · 统一 Demo（标准DEMO + 客户化规划器 双模式）
============================================================
叙事顺序贴合正常思维：
  ① 标准DEMO  —— 先讲清"我们的智能数字孪生长什么样"：以单一标杆参考工厂
                  （机加工精密产线）为主角，展示 几何3D / 实时传感 / 工厂仿真 / 数据底座 四面板。
  ② 客户定制  —— 同一套引擎，输入 公司/产品 + 客户参数，自动判定工厂原型、
                  按节拍反算设备、仿真验证产能，并复用标准引擎渲染"您的工厂实景"。

零依赖路径（对标说明见 README.md）：
  几何(numpy/plotly→真OCCT) + 数据(SQLite队列≈EMQX+IoTDB)
  + 智能(规则→MAS+本地LLM) + 工厂级(SimPy) + 规划器(planner_core)
  无云 / 无编译 / 无 GPU。

运行：streamlit run demo_unified.py --server.port 8505
"""
import os
import time
import random
import threading
from collections import deque
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import factory_sim_core as fs
import planner_core as pc
import demo_app as da   # 复用几何/传感/3D/数据底座渲染函数

# 复用 demo_app 的配色与渲染原语
BLUE = da.BLUE
ORANGE = da.ORANGE
GREEN = da.GREEN
SOFT_BG = da.SOFT_BG
CARD_BORDER = da.CARD_BORDER

# 形状中文名（供面板标题）
SHAPE_NAMES = {
    "machining": "CNC车床", "assembly": "装备柜",
    "semiconductor": "晶圆+腔室", "automotive": "车身轮廓",
    "electronics": "PCB+元器件",
}
# 标杆参考工厂（标准DEMO主角）
FLAGSHIP = "machining"

HERE = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# 后台传感线程（全局只起一次，标准/定制两模式共享）
# ============================================================
def ensure_simulator():
    if 'sim_started' not in st.session_state:
        t = threading.Thread(target=da.simulator, daemon=True)
        t.start()
        st.session_state['sim_started'] = True
    da.preload_data(da.PRELOAD_N)
    da.drain_queue()


# ============================================================
# 缓存数据底座预览（避免每轮 sleep 2.5s，首屏加速）
# ============================================================
@st.cache_data(show_spinner=False)
def _cached_databus():
    """数据底座回查：只算一次，后续复用缓存。"""
    return da.render_databus_preview()


# ============================================================
# 通用卡片 / 面板组件
# ============================================================
def kpi_card(value, label, idx_color=BLUE):
    return (
        f'<div style="border:1px solid {CARD_BORDER};border-radius:10px;padding:14px;'
        f'text-align:center;background:{SOFT_BG};">'
        f'<div style="font-size:22px;font-weight:800;color:{idx_color};">{value}</div>'
        f'<div style="font-size:11px;color:#6b7280;margin-top:3px;">{label}</div></div>'
    )


def panel_geometry(factory_type):
    V, F = da.build_factory_shape(factory_type)
    gm = da.geometry_metrics(V)
    sn = SHAPE_NAMES.get(factory_type, "设备")
    st.markdown(
        f'<div style="font-size:14px;font-weight:600;color:{BLUE};margin:8px 0 6px;">'
        f'① 数字实体 · 几何模型（{sn}）</div>', unsafe_allow_html=True)
    st.plotly_chart(da.render_3d(V, F), width='stretch')
    st.caption(f'按工厂类型「{fs.get_factory_spec(factory_type)["display"]}」生成标志性 3D 形态；'
               f'顶点数 {gm["顶点数"]}；正式版换 OGG/OCCT 真实模型。')


def panel_sensor():
    st.markdown(
        f'<div style="font-size:14px;font-weight:600;color:{BLUE};margin:8px 0 6px;">'
        f'② 实时孪生互动 · 传感器时序</div>', unsafe_allow_html=True)
    sfig = da.render_sensor_chart()
    if sfig:
        st.plotly_chart(sfig, width='stretch')
        latest_temp = list(da.data_buf['temp'])[-1] if da.data_buf['temp'] else 45
        if latest_temp > 54:
            st.caption(f'⚠️ 第 {len(da.data_buf["t"])} 点温度尖峰({latest_temp:.1f}°C)将触发规则引擎告警！')
        else:
            st.caption(f'当前最新温度 {latest_temp:.1f}°C（正常范围 43–48°C）。')
    else:
        st.info('采集启动中…')


def panel_factory_util(sim_dict, factory_type, title_suffix=""):
    names = list(sim_dict["station_util"].keys())
    vals = list(sim_dict["station_util"].values())
    fig = go.Figure(data=[go.Bar(
        x=names, y=vals,
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
    st.markdown(
        f'<div style="font-size:14px;font-weight:600;color:{BLUE};margin:8px 0 6px;">'
        f'③ 工厂级仿真 · {fs.get_factory_spec(factory_type)["display"]} 各工位利用率{title_suffix}</div>',
        unsafe_allow_html=True)
    st.plotly_chart(fig, width='stretch')
    st.caption(f'场景①新建厂验证：产能 {sim_dict["throughput_per_h"]} 件/时 · '
               f'瓶颈 {sim_dict["bottleneck"]} · '
               f'设计产能可达性 {sim_dict.get("reachability", 0)*100:.1f}%')


# ============================================================
# 模式①：标准DEMO（单一标杆参考工厂为主角）
# ============================================================
def render_standard():
    st.markdown(
        '<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;'
        'padding:12px 16px;margin-bottom:14px;font-size:13px;color:#1e40af;">'
        '📌 <b>标准DEMO</b>：这是我们「智能数字孪生系统」的参考实现 —— 以一条机加工精密产线为标杆，'
        '完整展示 几何建模 → 实时同步 → 智能诊断 → 工厂级仿真 → 数据底座 的闭环。'
        '看懂这套标准能力后，切到「客户定制」即可把它落到您自己的工厂。</div>',
        unsafe_allow_html=True)

    # 探索其它类型（次要入口，不作为主角）
    fmt_map = dict(fs.list_factories())
    explore = st.selectbox(
        "🔍 探索其它工厂类型（标准能力可覆盖的类型）",
        options=list(fmt_map.keys()),
        index=list(fmt_map.keys()).index(FLAGSHIP),
        format_func=lambda k: fmt_map.get(k, k),
        key='std_explore',
    )
    ft = explore

    # KPI 一行四卡（仅算一次数据底座回查，缓存）
    V, F = da.build_factory_shape(ft)
    gm = da.geometry_metrics(V)
    db_fig, db_n = _cached_databus() or (None, da.PRELOAD_N)
    fres = fs.simulate_new_plant(factory_type=ft)
    sync_ms = random.randint(38, 115)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(kpi_card(gm["顶点数"], "几何顶点(占位)"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card(f"≤{sync_ms}ms", "同步延迟基准"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card(db_n if db_n else da.PRELOAD_N, "数据底座落库点"), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card(f'{fres["bottleneck_util"]:.3f}', "工厂级瓶颈利用率"), unsafe_allow_html=True)

    # 四面板 2×2
    g1, g2 = st.columns(2)
    g3, g4 = st.columns(2)
    with g1:
        panel_geometry(ft)
    with g2:
        panel_sensor()
    with g3:
        panel_factory_util(fres, ft)
    with g4:
        st.markdown(
            f'<div style="font-size:14px;font-weight:600;color:{BLUE};margin:8px 0 6px;">'
            f'④ 数据底座 · SQLite 回查时序</div>', unsafe_allow_html=True)
        if db_fig:
            st.plotly_chart(db_fig, width='stretch')
            st.caption(f'真实调用 DataBusLite→TsStore 落库后回查（{db_n}点 ≈EMQX→IoTDB）。')
        else:
            st.info('数据底座回查加载中…')

    # 智能告警
    st.markdown('<br>')
    alarms_now = da.rule_engine(
        da.data_buf['temp'][-1] if da.data_buf['temp'] else 45,
        da.data_buf['vib'][-1] if da.data_buf['vib'] else 0.8,
        da.data_buf['rpm'][-1] if da.data_buf['rpm'] else 1500,
    )
    if alarms_now:
        for name, desc in alarms_now:
            st.warning(f'**{name}**：{desc}')
    else:
        st.success('✅ 设备工况正常，未检测到异常。')

    # 建设方案要点（标杆厂）
    st.divider()
    spec = fs.get_factory_spec(ft)
    st.markdown(f'### 🏭 本厂数字孪生建设方案要点（{spec["display"]}）')
    a1, a2 = st.columns(2)
    with a1:
        st.markdown('**数字孪生建模重点**')
        st.write(spec["dt_focus"])
        st.markdown('**行业痛点 / 优化重点**')
        for x in spec["pain_points"]:
            st.write(f'• {x}')
    with a2:
        st.markdown('**仿真验证建议**')
        st.write(spec["recommend"])
        st.markdown('**原型说明**')
        st.write(spec["desc"])

    st.caption('本 Demo 用意：在最低硬件上证明"几何建模→实时同步→智能诊断"闭环可行。'
               '正式构建时几何换 OGG/OCCT、数据换 EMQX+IoTDB、智能换通用 MAS+本地 LLM，架构不变。'
               '数值为概念验证占位，不构成 GB/T 合规证据。')


# ============================================================
# 模式②：客户定制（复用标准引擎落到客户工厂）
# ============================================================
def render_custom():
    st.markdown(
        '<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;'
        'padding:12px 16px;margin-bottom:14px;font-size:13px;color:#1e40af;">'
        '📌 <b>客户定制</b>：复用上面那套标准数字孪生引擎。填入贵司/产品与关键参数，'
        '系统自动判定工厂原型、按节拍反算设备、仿真验证产能，并直接复用标准引擎渲染「您的工厂实景」。'
        '标准蓝图 + 您的参数 = 您的方案。</div>',
        unsafe_allow_html=True)

    # 输入区
    c1, c2 = st.columns(2)
    with c1:
        company = st.text_input("公司名称（选填）", placeholder="如：示例新能源科技", key="c_company")
        website = st.text_input("公司网站/网址（选填，由助理代查）", placeholder="https://...", key="c_website")
    with c2:
        product = st.text_area(
            "核心产品 / 生产工艺描述（必填，驱动工厂类型判定）",
            placeholder="如：新能源汽车动力电池包，含电芯模组、BMS、结构件与总装",
            height=100, key="c_product",
        )

    st.markdown("### ⚙️ 客户参数（向客户采集，驱动设备反算）")
    p1, p2, p3, p4, p5, p6 = st.columns(6)
    annual = p1.number_input("目标年产量(万件/年)", 1.0, 10000.0, 100.0, 1.0, key="c_annual")
    shifts = p2.selectbox("班制", [1, 2, 3], index=1, key="c_shifts")
    wdays = p3.number_input("年工作天数", 50, 365, 250, 1, key="c_wdays")
    hps = p4.number_input("每班工时", 4, 24, 8, 1, key="c_hps")
    footprint = p5.number_input("厂房面积(㎡,选填)", 0, 200000, 0, 500, key="c_fp")
    automation = p6.number_input("自动化率(%,选填)", 0, 100, 0, 5, key="c_auto")

    run = st.button("🚀 生成客户化规划", type="primary", use_container_width=True, key="c_run")

    if run:
        if not product.strip():
            st.error("请至少填写『核心产品/生产工艺描述』，这是工厂类型判定的依据。")
            st.stop()
        params = {
            "annual_volume_wan": annual, "shifts": shifts, "working_days": wdays,
            "hours_per_shift": hps,
            "footprint": footprint if footprint > 0 else "",
            "automation": automation if automation > 0 else "",
        }
        with st.spinner("正在判定工厂原型并仿真验证…"):
            plan = pc.derive_plan(company=company, website=website, product=product, params=params)
        st.session_state["c_plan"] = plan

    if "c_plan" in st.session_state:
        plan = st.session_state["c_plan"]
        sim = plan["sim"]

        st.success(f"✅ 推荐工厂原型：**{plan['type_display']}**　｜　{plan['detect_reason']}")

        # KPI 五行
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("系统节拍 T", f"{plan['takt_T']:.3f} 分/件")
        k2.metric("目标产能", f"{plan['target_cap_h']:.1f} 件/时")
        k3.metric("产能(仿真)", f"{sim['throughput_per_h']:.1f} 件/时")
        k4.metric("产线平衡率", f"{sim['line_balance_rate']*100:.1f}%")
        k5.metric("产能可达性", f"{(sim.get('reachability') or 0)*100:.1f}%")

        # 工艺路线 + 设备表
        st.markdown(f"**工艺路线**：{plan['process_flow']}")
        df = pd.DataFrame(
            [(n, f"{m:.2f}", c) for (n, m, s, c) in plan["derived_stations"]],
            columns=["工位", "节拍(分)", "机器数"],
        )
        st.markdown(f"**设备配置（按节拍反算，合计 {plan['total_machines']} 台）**")
        st.dataframe(df, use_container_width=True, hide_index=True)

        # 敏感性
        up = plan["sim_uplift20"]
        st.warning(
            f"📈 敏感性：产量 +20% 时可达性降至 {(up.get('reachability') or 0)*100:.1f}%，"
            f"瓶颈 → {up['bottleneck']}，建议对瓶颈工位预留扩产余量。"
        )

        # 方案要点
        st.markdown("---")
        st.markdown("### 📋 本厂数字孪生建设方案要点")
        a1, a2 = st.columns(2)
        with a1:
            st.markdown("**数字孪生建模重点**")
            st.write(plan["dt_focus"])
            st.markdown("**行业痛点 / 优化重点**")
            for x in plan["pain_points"]:
                st.write(f"• {x}")
        with a2:
            st.markdown("**仿真验证建议**")
            st.write(plan["recommend"])
            st.markdown("**需客户补充的真实数据**")
            st.caption("BOM与标准工时、厂房图纸与物流尺寸、设备OEE/故障率、MES/SCADA接口、品质检测项目")

        # 🔗 同一套引擎：您的工厂实景（复用标准面板）
        st.divider()
        st.markdown("### 🔗 同一套数字孪生引擎 · 您的工厂实景")
        st.caption("下方直接复用「标准DEMO」的几何与仿真引擎，输入即您的工厂参数 —— 标准能力无需重写，只是换了数据。")
        m1, m2 = st.columns(2)
        with m1:
            panel_geometry(plan["type_key"])
        with m2:
            panel_factory_util(sim, plan["type_key"], title_suffix="（推导配置）")
        # 传感（通用，复用标准引擎）
        panel_sensor()

        # 下载规划书
        html = pc.render_plan_html(plan)
        st.download_button("📄 下载规划书 HTML", html, file_name="客户化工厂规划书.html", mime="text/html")
        st.caption("注：本 Demo 数值为概念验证，不构成 GB/T 45873-2025 合规证据；正式合规走 CESI 测评。")
    else:
        st.info("填写上方信息后点击「生成客户化规划」。示例：产品填『新能源汽车动力电池包』，年产量 50 万件，2 班制。")


# ============================================================
# 入口
# ============================================================
def main():
    st.set_page_config(
        page_title='智能数字孪生 · 统一Demo（标准+定制）',
        layout='wide',
        menu_items={'About': '标准DEMO + 客户化规划器：几何(numpy/plotly) + 数据(SQLite队列≈EMQX+IoTDB) + 智能(规则→MAS) + 工厂级(SimPy) + 规划器。无云/无编译/无GPU'},
    )

    st.markdown(
        '<div style="border-bottom:3px solid #2563eb;padding-bottom:10px;margin-bottom:14px">'
        '<h1 style="margin:0;font-size:22px;">⚡ 智能数字孪生系统 · 统一 Demo</h1>'
        '<p style="margin:4px 0 0;color:#6b7280;font-size:12px;">'
        '先看清「我们的标准数字孪生」→ 再把它定制到「您的工厂」</p></div>',
        unsafe_allow_html=True)

    # 顶部模式切换（标准DEMO 默认在前）
    mode = st.radio(
        "展示模式",
        options=["标准DEMO", "客户定制"],
        index=0,
        horizontal=True,
        key="mode",
    )

    # 传感线程全局只起一次（两模式共享实时数据）
    ensure_simulator()

    if mode == "标准DEMO":
        render_standard()
    else:
        render_custom()

    # 自动刷新（每 3 秒，降低 CPU 占用 + 避免首屏超时）
    time.sleep(3.0)
    st.rerun()


if __name__ == "__main__":
    main()
