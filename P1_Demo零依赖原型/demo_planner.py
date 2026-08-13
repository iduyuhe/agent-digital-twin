# -*- coding: utf-8 -*-
"""
客户化工厂规划器 · 零依赖 Demo（Streamlit，端口 8504）
==================================================
输入：公司名称 / 网站 / 产品描述 + 客户参数（年产量·班制·节拍·占地·自动化率）
输出：工厂原型判定 → 工艺路线 → 设备配置(节拍反算) → 仿真验证 → 建设方案要点 → 可下载规划书

依赖：pip install streamlit plotly numpy pandas simpy
运行：streamlit run demo_planner.py --server.port 8504
"""
import streamlit as st
import plotly.graph_objects as go
import planner_core as pc


st.set_page_config(page_title="客户化工厂规划器", layout="wide")
st.title("客户化工厂数字孪生规划器")
st.caption(
    "给公司/产品 + 关键参数，自动推导工厂类型、按节拍反算设备配置、仿真验证产能，并生成可下载规划书。"
    "降依赖路径：SimPy 仿真 + 工厂类型库（免商业引擎、免云）。"
)

# ------------------------------------------------------------
# 输入区
# ------------------------------------------------------------
c1, c2 = st.columns(2)
with c1:
    company = st.text_input("公司名称（选填）", placeholder="如：示例新能源科技")
    website = st.text_input("公司网站/网址（选填，由助理代查）", placeholder="https://...")
with c2:
    product = st.text_area(
        "核心产品 / 生产工艺描述（必填，驱动工厂类型判定）",
        placeholder="如：新能源汽车动力电池包，含电芯模组、BMS、结构件与总装",
        height=100,
    )

st.markdown("### ⚙️ 客户参数（向客户采集，驱动设备反算）")
p1, p2, p3, p4, p5, p6 = st.columns(6)
annual = p1.number_input("目标年产量(万件/年)", 1.0, 10000.0, 100.0, 1.0)
shifts = p2.selectbox("班制", [1, 2, 3], index=1)
wdays = p3.number_input("年工作天数", 50, 365, 250, 1)
hps = p4.number_input("每班工时", 4, 24, 8, 1)
footprint = p5.number_input("厂房面积(㎡,选填)", 0, 200000, 0, 500)
automation = p6.number_input("自动化率(%,选填)", 0, 100, 0, 5)

run = st.button("🚀 生成客户化规划", type="primary", use_container_width=True)

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
    plan = pc.derive_plan(company=company, website=website, product=product, params=params)
    st.session_state["plan"] = plan

# ------------------------------------------------------------
# 结果区
# ------------------------------------------------------------
if "plan" in st.session_state:
    plan = st.session_state["plan"]
    sim = plan["sim"]

    # 判定条
    st.success(
        f"✅ 推荐工厂原型：**{plan['type_display']}**　｜　{plan['detect_reason']}"
    )

    # KPI
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("系统节拍 T", f"{plan['takt_T']:.3f} 分/件")
    k2.metric("目标产能", f"{plan['target_cap_h']:.1f} 件/时")
    k3.metric("产能(仿真)", f"{sim['throughput_per_h']:.1f} 件/时")
    k4.metric("产线平衡率", f"{sim['line_balance_rate']*100:.1f}%")
    k5.metric("产能可达性", f"{(sim.get('reachability') or 0)*100:.1f}%")

    # 工艺路线 + 设备表
    st.markdown(f"**工艺路线**：{plan['process_flow']}")
    df = __import__("pandas").DataFrame(
        [(n, f"{m:.2f}", c) for (n, m, s, c) in plan["derived_stations"]],
        columns=["工位", "节拍(分)", "机器数"],
    )
    st.markdown(f"**设备配置（按节拍反算，合计 {plan['total_machines']} 台）**")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # 利用率图
    names = list(sim["station_util"].keys())
    vals = list(sim["station_util"].values())
    fig = go.Figure(go.Bar(x=names, y=vals, marker_color="#2563eb",
                           text=[f"{v*100:.1f}%" for v in vals], textposition="outside"))
    fig.update_layout(title="各工位利用率（推导配置）", yaxis_title="利用率",
                      yaxis_range=[0, 1.1], height=340, margin=dict(l=40, r=20, t=40, b=30))
    st.plotly_chart(fig, use_container_width=True)

    # 敏感性
    up = plan["sim_uplift20"]
    st.warning(
        f"📈 敏感性：产量 +20% 时可达性降至 {(up.get('reachability') or 0)*100:.1f}%，"
        f"瓶颈 → {up['bottleneck']}，建议对瓶颈工位预留扩产余量。"
    )

    # 方案要点
    st.markdown("---")
    st.subheader("📋 本厂数字孪生建设方案要点")
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

    # 下载规划书
    html = pc.render_plan_html(plan)
    st.download_button("📄 下载规划书 HTML", html, file_name="客户化工厂规划书.html", mime="text/html")

    st.caption("注：本 Demo 数值为概念验证，不构成 GB/T 45873-2025 合规证据；正式合规走 CESI 测评。")
else:
    st.info("填写上方信息后点击「生成客户化规划」。示例：产品填『新能源汽车动力电池包』，年产量 50 万件，2 班制。")
