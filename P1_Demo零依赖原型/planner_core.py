# -*- coding: utf-8 -*-
"""
客户化工厂规划核心 · planner_core
================================
把"5 套固定工厂模板"升级为：输入 公司/产品/参数 → 输出客户化工厂规划。

两条入口：
  A. 公司名/网址 + 产品描述  → 推断工厂原型 + 自动建议
  B. 产品名 + 客户填参（年产量/班制/节拍/占地/自动化率） → 反算设备配置 + 仿真验证

核心公式：
  系统节拍 T = 年可用工时 / 目标年产量          （分/件）
  各工位需求机器数 c = ceil(工位节拍 m / T)      （向上取整，至少 1）
  设计产能(件/时) = 60 / T

依赖 factory_sim_core（SimPy 仿真 + 工厂类型库）。纯 Python，可在本地 Streamlit 运行。
"""
import math
import factory_sim_core as fs


# ============================================================
# 1. 产品/公司文本 → 工厂原型判定（关键词映射）
# ============================================================
_TYPE_KEYWORDS = {
    "machining": ["机加工", "精密加工", "五金", "模具", "cnc", "切削", "零部件", "零件", "铸件", "锻件", "轴", "齿轮"],
    "assembly": ["装备", "机电", "工程机械", "大型设备", "整机", "成套", "电气柜", "变压器", "电机", "泵", "减速机"],
    "semiconductor": ["芯片", "晶圆", "半导体", "ic", "封测", "光刻", "集成电路", "电子元件", "sensor", "传感器芯片"],
    "automotive": ["汽车", "整车", "车身", "发动机", "车桥", "变速箱", "冲压", "焊装", "涂装", "电池包", "线束", "车灯"],
    "electronics": ["手机", "消费电子", "pcb", "smt", "智能硬件", "家电", "可穿戴", "路由器", "模组", "充电器", "锂电池", "光伏"],
}


def detect_factory_type(text):
    """返回 (type_key, 置信度说明)。多关键词命中取最高分；无命中回退 electronics。"""
    t = (text or "").lower()
    score = {k: 0 for k in _TYPE_KEYWORDS}
    for k, kws in _TYPE_KEYWORDS.items():
        for kw in kws:
            if kw.lower() in t:
                score[k] += 1
    best = max(score, key=score.get)
    if score[best] == 0:
        return "electronics", "未识别到明确行业关键词，默认按『电子组装工厂』原型推导（请在表单中校正行业）。"
    reason = "命中关键词：" + "、".join(
        kw for kw in _TYPE_KEYWORDS[best] if kw.lower() in t
    )
    return best, reason


# ============================================================
# 2. 客户参数 → 反算设备配置 + 仿真验证
# ============================================================
def derive_plan(company="", website="", product="", params=None):
    """
    params: dict{
      annual_volume_wan: 目标年产量(万件/年),
      shifts: 班制(1/2/3),
      working_days: 年工作天数(默认250),
      hours_per_shift: 每班工时(默认8),
      footprint: 厂房面积(㎡, 可选),
      automation: 自动化率(%, 可选),
    }
    返回完整规划 dict，供 UI 与 HTML 导出复用。
    """
    params = params or {}
    annual_wan = float(params.get("annual_volume_wan", 100))
    shifts = int(params.get("shifts", 2))
    wdays = int(params.get("working_days", 250))
    hps = int(params.get("hours_per_shift", 8))
    footprint = params.get("footprint") or ""
    automation = params.get("automation") or ""

    annual_items = annual_wan * 10000.0
    total_minutes = wdays * shifts * hps * 60.0
    T = total_minutes / annual_items if annual_items > 0 else 1.0  # 系统节拍(分/件)
    target_cap_h = 60.0 / T if T > 0 else 0.0  # 设计产能(件/时)

    # 工厂原型
    type_key, reason = detect_factory_type(product or company)
    spec = fs.get_factory_spec(type_key)
    display = spec["display"]

    # 反算各工位机器数
    derived_stations = []
    for (n, m, s, c0) in spec["stations"]:
        need = max(1, math.ceil(m / T)) if T > 0 else c0
        need = min(need, 24)  # 单工位封顶，防极端值
        derived_stations.append((n, m, s, need))

    # 仿真验证（到达间隔=系统节拍，验证该配置能否满足需求）
    sim = fs.simulate_new_plant(
        factory_type=type_key,
        stations_spec=derived_stations,
        arrival_interval=T,
        sim_minutes=wdays * shifts * hps * 60.0,
        designed_capacity_per_h=target_cap_h,
    )
    # 敏感性：产能 +20% 时是否仍能达
    sim_up = fs.simulate_new_plant(
        factory_type=type_key,
        stations_spec=derived_stations,
        arrival_interval=T / 1.2,
        sim_minutes=wdays * shifts * hps * 60.0,
        designed_capacity_per_h=target_cap_h * 1.2,
    )

    total_machines = sum(c for (_, _, _, c) in derived_stations)

    plan = {
        "company": company,
        "website": website,
        "product": product,
        "type_key": type_key,
        "type_display": display,
        "detect_reason": reason,
        "params": {
            "annual_volume_wan": annual_wan, "shifts": shifts, "working_days": wdays,
            "hours_per_shift": hps, "footprint": footprint, "automation": automation,
        },
        "takt_T": T,
        "target_cap_h": target_cap_h,
        "derived_stations": derived_stations,
        "total_machines": total_machines,
        "process_flow": " → ".join(n for n, _, _, _ in derived_stations),
        "sim": sim,
        "sim_uplift20": sim_up,
        "dt_focus": spec.get("dt_focus", ""),
        "pain_points": spec.get("pain_points", []),
        "recommend": spec.get("recommend", ""),
        "desc": spec.get("desc", ""),
    }
    return plan


# ============================================================
# 3. 规划书 HTML 导出
# ============================================================
def render_plan_html(plan):
    p = plan["params"]
    sim = plan["sim"]
    flow = plan["process_flow"]
    rows = "".join(
        f"<tr><td>{n}</td><td>{m:.2f}</td><td>{c}</td></tr>"
        for (n, m, s, c) in plan["derived_stations"]
    )
    pains = "".join(f"<li>{x}</li>" for x in plan["pain_points"])
    html = f"""<html><head><meta charset="utf-8">
<style>
 body{{font-family:-apple-system,'Segoe UI',sans-serif;color:#1f2937;max-width:900px;margin:24px auto;padding:0 20px;}}
 h1{{color:#2563eb;font-size:24px;border-bottom:3px solid #2563eb;padding-bottom:8px;}}
 h2{{color:#2563eb;font-size:17px;margin-top:28px;border-left:4px solid #2563eb;padding-left:10px;}}
 .kv{{background:#f8fafc;border:1px solid #e5e7eb;border-radius:8px;padding:14px 18px;margin:10px 0;}}
 .kv span{{display:inline-block;min-width:120px;color:#6b7280;}}
 table{{width:100%;border-collapse:collapse;margin-top:8px;}}
 th{{background:#2563eb;color:#fff;padding:8px 10px;text-align:left;font-size:13px;}}
 td{{border:1px solid #e5e7eb;padding:7px 10px;font-size:13px;}}
 tr:nth-child(even){{background:#f1f5f9;}}
 .big{{font-size:30px;font-weight:800;color:#2563eb;}}
 .num4{{display:flex;gap:12px;margin:10px 0;}}
 .num4 div{{flex:1;background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:12px;text-align:center;}}
 .num4 b{{display:block;font-size:22px;color:#2563eb;}}
 .warn{{background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:12px 16px;color:#92400e;}}
 .foot{{color:#9ca3af;font-size:12px;margin-top:30px;border-top:1px solid #e5e7eb;padding-top:10px;}}
</style></head><body>
<h1>客户化工厂数字孪生规划书</h1>
<div class="kv">
 <div><span>委托方</span>{plan['company'] or '（待填）'}</div>
 <div><span>官方网站</span>{plan['website'] or '（待填）'}</div>
 <div><span>核心产品</span>{plan['product'] or '（待填）'}</div>
 <div><span>规划日期</span>2026-08-13</div>
</div>

<h2>一、工厂类型判定</h2>
<div class="kv">
 <div><span>推荐原型</span><b style="color:#2563eb">{plan['type_display']}</b></div>
 <div><span>判定依据</span>{plan['detect_reason']}</div>
 <div><span>原型说明</span>{plan['desc']}</div>
</div>

<h2>二、客户化参数</h2>
<div class="kv">
 <div><span>目标年产量</span>{p['annual_volume_wan']:.0f} 万件/年</div>
 <div><span>班制</span>{p['shifts']} 班/天　<span>年工作</span>{p['working_days']} 天　<span>每班</span>{p['hours_per_shift']} h</div>
 <div><span>厂房面积</span>{p['footprint'] or '（待客户补充）'} ㎡　<span>自动化率</span>{p['automation'] or '（待客户补充）'} %</div>
 <div><span>系统节拍 T</span>{plan['takt_T']:.3f} 分/件　<span>目标产能</span>{plan['target_cap_h']:.1f} 件/时</div>
</div>

<h2>三、工艺路线</h2>
<p style="font-size:15px;">{flow}</p>

<h2>四、设备配置（按节拍反算）</h2>
<table><tr><th>工位</th><th>节拍(分)</th><th>机器数</th></tr>{rows}</table>
<p>合计设备 <b>{plan['total_machines']}</b> 台（按系统节拍反算：机器数 = ⌈工位节拍 / 系统节拍⌉）。</p>

<h2>五、仿真验证（SimPy 概念验证）</h2>
<div class="num4">
 <div><b>{sim['throughput_per_h']:.1f}</b>产能(件/时)</div>
 <div><b>{sim['line_balance_rate']*100:.1f}%</b>产线平衡率</div>
 <div><b>{sim['bottleneck']}</b>瓶颈工位</div>
 <div><b>{(sim.get('reachability') or 0)*100:.1f}%</b>产能可达性</div>
</div>
<p>敏感性：当产量提升 20% 时，可达性降至 <b>{(plan['sim_uplift20'].get('reachability') or 0)*100:.1f}%</b>，
瓶颈 → <b>{plan['sim_uplift20']['bottleneck']}</b>，提示需对瓶颈工位预留扩产余量。</p>

<h2>六、数字孪生建设方案要点</h2>
<div class="kv"><div><span>建模重点</span>{plan['dt_focus']}</div></div>
<div class="kv"><div><span>行业痛点</span><ul>{pains}</ul></div></div>
<div class="kv"><div><span>仿真建议</span>{plan['recommend']}</div></div>

<h2>七、需客户补充的真实数据</h2>
<div class="warn">
 • 产品 BOM 与单件标准工时（用于校核工位节拍 m）<br>
 • 厂房建筑图纸与物流通道尺寸（用于布局与搬运仿真）<br>
 • 设备真实 OEE / 故障率（用于可靠性与可用性建模）<br>
 • MES/SCADA 数据接口（用于实时数据底座接入，见 DataSource 适配层）<br>
 • 品质标准与检测项目（用于虚拟检测工位规则配置）
</div>

<p class="foot">本规划书由零依赖 Demo 自动生成，数值为概念验证，不构成 GB/T 45873-2025 合规证据；正式合规走 CESI 测评。
工业5点0产业生态联盟 · 数字孪生规划助手。</p>
</body></html>"""
    return html


if __name__ == "__main__":
    # 自测：给一个产品，看能否推导出合理规划
    import json
    plan = derive_plan(
        company="示例新能源科技", website="https://example.com",
        product="新能源汽车动力电池包，含电芯模组、BMS、结构件与总装",
        params={"annual_volume_wan": 50, "shifts": 2, "working_days": 300, "hours_per_shift": 8,
                "footprint": 20000, "automation": 70},
    )
    print("工厂原型:", plan["type_display"])
    print("判定依据:", plan["detect_reason"])
    print("系统节拍 T:", round(plan["takt_T"], 3), "分/件  目标产能:", round(plan["target_cap_h"], 1), "件/时")
    print("工艺路线:", plan["process_flow"])
    print("设备配置:", [(n, c) for (n, m, s, c) in plan["derived_stations"]])
    print("仿真产能:", plan["sim"]["throughput_per_h"], "可达性:", round((plan["sim"].get("reachability") or 0)*100, 1), "%")
    print("PLANNER_OK")
