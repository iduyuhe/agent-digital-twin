# -*- coding: utf-8 -*-
"""
行业模板库 · industry_templates
================================
基于 5 类工厂原型（factory_sim_core.FACTORY_LIBRARY）沉淀**可复用的客户化规划模板层**。

定位：把"工厂仿真原型"升级为"行业规划模板"——每个行业模板包含：
  · 行业画像（标签 / 细分领域 / 典型产品）
  · 典型客户参数预设（一键套用到客户定制模式）
  · 参考 KPI 基准（节拍 / 产能 / 设备数 / 几何精度）
  · 规划假设说明（让规划书可追溯、可校正）
  · 数字孪生成熟度目标等级（L1~L3）
  · 行业标杆参考指标

用途：
  · 客户定制模式 → 选行业模板 → 一键预填产品描述 + 客户参数 → 直接生成规划书
  · 外部复用 → export_templates_json() 导出 JSON，供销售/方案团队离线编辑行业包

零依赖：纯 Python dict + json，无第三方库。依赖 factory_sim_core（拿工厂原型基线）。
"""
import json
import factory_sim_core as fs


# ============================================================
# 行业规划模板（对 FACTORY_LIBRARY 的"规划层"增强）
# 说明：display / stations / dt_focus / pain_points / recommend 等基础字段
#      仍在 factory_sim_core.FACTORY_LIBRARY，这里只补充"规划模板"专属字段。
# ============================================================
INDUSTRY_TEMPLATES = {
    "machining": {
        "industry_tags": ["精密制造", "金属加工", "多品种小批量"],
        "sub_sectors": ["通用机械零部件", "航空航天结构件", "医疗器械零件", "汽车精密铸件"],
        "typical_products": [
            "精密齿轮箱壳体", "液压阀体", "航空铝合金支架", "注塑模具模仁",
        ],
        "twin_target_level": "L2（制造孪生：工序级时间 + 设备状态）",
        "typical_params": {
            "annual_volume_wan": 30, "shifts": 2, "working_days": 250,
            "hours_per_shift": 8, "footprint": 12000, "automation": 55,
            "product_hint": "精密机械零部件，多品种小批量，含 CNC 粗精加工、热处理与三坐标检测",
        },
        "planning_assumptions": [
            "工位节拍取自通用机加工艺基准，正式规划需以客户 BOM 标准工时为输入校核",
            "设备数按系统节拍反算并含 ~10% 缓冲，应对换型(set-up)与刀具故障损失",
            "几何孪生精度目标 ≤0.5mm 以匹配加工公差（见 P2-B CAE 保真标尺）",
        ],
        "benchmark": "参考通用机械行业设备综合 OEE 75%~85%，换型损失占比常达 15%~25%",
    },
    "assembly": {
        "industry_tags": ["装备总装", "机电", "长周期"],
        "sub_sectors": ["工程机械", "电气成套设备", "工业电机/泵/减速机", "能源装备"],
        "typical_products": [
            "大型工程机械整机", "高低压电气柜", "工业减速机", "风电变流器",
        ],
        "twin_target_level": "L2（制造孪生：BOM 齐套 + 长周期工序时间）",
        "typical_params": {
            "annual_volume_wan": 5, "shifts": 2, "working_days": 250,
            "hours_per_shift": 8, "footprint": 30000, "automation": 40,
            "product_hint": "大型机电装备总装，含部装、总装、线缆敷设、调试与出厂检验，节拍长",
        },
        "planning_assumptions": [
            "装配节拍长、周期大，按工序级时间建模而非单件流水线",
            "设备数反算偏保守（长周期工位易因齐套停等，需额外缓冲工位）",
            "孪生重点在 BOM 齐套状态与调试返工回路，而非单纯产能",
        ],
        "benchmark": "参考装备制造业，物料齐套率每提升 5% 可释放 8%~12% 在制产能",
    },
    "semiconductor": {
        "industry_tags": ["晶圆制造", "重入式", "高价值设备"],
        "sub_sectors": ["逻辑/存储 Fab", "功率器件", "封测厂", "MEMS 传感器"],
        "typical_products": [
            "12 寸逻辑晶圆", "功率半导体模组", "先进封装晶圆", "MEMS 传感器芯片",
        ],
        "twin_target_level": "L3（预测孪生：机台 OEE + 良率联合预测）",
        "typical_params": {
            "annual_volume_wan": 20, "shifts": 3, "working_days": 330,
            "hours_per_shift": 8, "footprint": 50000, "automation": 95,
            "product_hint": "半导体晶圆制造，含光刻、刻蚀、薄膜沉积、离子注入、CMP 与检测，重入式工艺",
        },
        "planning_assumptions": [
            "设备单台价值亿级，OEE 提升 1% 即巨额收益，孪生优先建模昂贵机台",
            "重入式工艺：同一 wafer 多次经过同机台，排程与产能需回路建模",
            "良率波动需工艺-设备联合孪生溯源，不能只看单工位吞吐",
        ],
        "benchmark": "参考头部 Fab 光刻机 OEE 目标 >90%，整体良率 95%~99.5%",
    },
    "automotive": {
        "industry_tags": ["整车总装", "刚性节拍", "混线生产"],
        "sub_sectors": ["乘用车整车厂", "商用车工厂", "动力电池包产线", "汽车零部件"],
        "typical_products": [
            "乘用车整车", "动力电池包(PACK)", "车桥/变速箱", "汽车线束总成",
        ],
        "twin_target_level": "L2（制造孪生：takt 主线 + 混线排序）",
        "typical_params": {
            "annual_volume_wan": 30, "shifts": 2, "working_days": 300,
            "hours_per_shift": 16, "footprint": 80000, "automation": 75,
            "product_hint": "汽车整车/部件流水线，含冲压、焊装、涂装、总装与质检，刚性节拍、混线生产",
        },
        "planning_assumptions": [
            "刚性节拍，整线 JPH(辆/时) 由瓶颈工位决定，按 takt 反算",
            "混线车型切换引入换型与排序复杂度，需 ANDON/PLC 数据接入",
            "涂装等高能耗工段能耗与节拍耦合，孪生需含能耗维度",
        ],
        "benchmark": "参考主流整车厂 JPH 30~60 辆/时，总装 OEE 目标 85%+",
    },
    "electronics": {
        "industry_tags": ["消费电子", "SMT", "多品种快节拍"],
        "sub_sectors": ["手机/PC 组装", "智能硬件", "锂电PACK", "光伏组件"],
        "typical_products": [
            "智能手机整机", "智能穿戴设备", "锂电池模组(PACK)", "光伏组件",
        ],
        "twin_target_level": "L2（制造孪生：SMT 节拍 + 测试良率）",
        "typical_params": {
            "annual_volume_wan": 100, "shifts": 3, "working_days": 300,
            "hours_per_shift": 8, "footprint": 20000, "automation": 80,
            "product_hint": "消费电子/SMT 组装，含 SMT 贴片、DIP 插件、回流焊、组装、ICT 测试与包装",
        },
        "planning_assumptions": [
            "SMT 节拍快、换线频繁，钢网/贴片程序准备时间是关键损失",
            "ICT/功能测试为典型瓶颈，测试工装切换需单独建模",
            "多品种小批量，齐套与排产复杂，孪生需含换线损失维度",
        ],
        "benchmark": "参考 EMS 行业 SMT 线体 OEE 70%~85%，换线损失可占 10%~20%",
    },
}


# ============================================================
# 对外 API
# ============================================================
def list_industry_templates():
    """返回 [(key, display, tags_str), ...]，供 UI 下拉使用。"""
    out = []
    for k in fs.FACTORY_ORDER:
        tpl = INDUSTRY_TEMPLATES.get(k, {})
        tags = " / ".join(tpl.get("industry_tags", []))
        out.append((k, fs.FACTORY_LIBRARY[k]["display"], tags))
    return out


def get_template(key):
    """返回某行业的完整模板 dict（合并工厂原型基线 + 规划层增强 + 动态参考 KPI）。"""
    if key not in fs.FACTORY_LIBRARY:
        raise KeyError(f"未知行业模板: {key}")
    base = fs.get_factory_spec(key)
    tpl = dict(INDUSTRY_TEMPLATES.get(key, {}))
    merged = dict(base)
    merged.update(tpl)
    # 动态参考 KPI（从 stations 计算，避免硬编码漂移）
    stations = base["stations"]
    total_machines = sum(c for (_, _, _, c) in stations)
    max_proc = max(m for (_, m, _, _) in stations)
    merged["reference_kpi"] = {
        "station_count": len(stations),
        "base_machine_count": total_machines,
        "longest_station_proc_min": round(max_proc, 2),
        "designed_capacity_per_h": base.get("new_plant", {}).get("designed_capacity_per_h"),
    }
    return merged


def apply_template(key, overrides=None):
    """
    套用行业模板 → 返回可直接喂给 planner_core.derive_plan 的入参。

    返回 dict:
      {
        "product": 预填的产品/工艺描述（含行业关键词，保判定一致）,
        "params": 典型客户参数 dict（可被 overrides 覆盖）,
        "type_override": key  （锁定工厂原型，避免描述微调导致的误判）,
      }
    """
    tpl = get_template(key)
    tp = dict(tpl["typical_params"])
    product = tp.pop("product_hint", "")
    params = {
        "annual_volume_wan": tp.get("annual_volume_wan", 100),
        "shifts": tp.get("shifts", 2),
        "working_days": tp.get("working_days", 250),
        "hours_per_shift": tp.get("hours_per_shift", 8),
        "footprint": tp.get("footprint", ""),
        "automation": tp.get("automation", ""),
    }
    if overrides:
        params.update(overrides)
    return {"product": product, "params": params, "type_override": key}


def export_templates_json(path=None):
    """导出全部行业模板为 JSON 字符串；若给 path 则同时写文件。"""
    data = {k: get_template(k) for k in fs.FACTORY_ORDER}
    s = json.dumps(data, ensure_ascii=False, indent=2)
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(s)
    return s


# ============================================================
# 自测
# ============================================================
if __name__ == "__main__":
    print("=== 行业模板库自测 ===")
    for k, disp, tags in list_industry_templates():
        tpl = get_template(k)
        ap = apply_template(k)
        print(f"[{k}] {disp} | 标签: {tags}")
        print(f"   典型产品: {tpl['typical_products']}")
        print(f"   孪生目标: {tpl['twin_target_level']}")
        print(f"   参考KPI: {tpl['reference_kpi']}")
        print(f"   预填产品: {ap['product'][:30]}... | 锁定原型: {ap['type_override']}")
        print(f"   典型参数: {ap['params']}")
    # 导出 JSON 自测
    js = export_templates_json()
    print(f"\n导出 JSON 字符数: {len(js)}（可离线复用行业包）")
    print("INDUSTRY_TEMPLATES_OK")
