# -*- coding: utf-8 -*-
"""
工厂级仿真核心 · SimPy 离散事件仿真（零依赖、免授权、免云）
============================================================
正式路径：工厂级仿真引擎 = Plant Simulation / AnyLogic / Simio（商业）
          + 国产 MES 仿真模块（见规划方案附录 B、P2 启动包构件 D）。
演示路径：用 SimPy（纯 Python 离散事件仿真库）零依赖实现"工厂级双场景"，
         免去商业引擎授权费用与云依赖，先把闭环跑通、验证建模逻辑，
         再按 POC 结论替换为商业引擎。

对应标准：GB/T 45873-2025 车间/工厂数字孪生（生产系统仿真·布局物流·产能）。

时间单位约定：内部仿真时钟以"分钟"为单位（proc_mean / arrival_interval / sim_minutes
均为分钟），对外输出产能换算为"件/小时"，便于与工业节拍直觉对齐。

双场景：
  场景① 新建工厂虚拟验证：在厂房/产线动工前，验证布局、产线平衡、产能可达性
  场景② 存量工厂产能优化：对运行工厂做瓶颈诊断、产能爬坡推演、增资回报推演

运行：
    python factory_sim_core.py        # 命令行跑双场景演示
    # 或在 demo_factory.py 中以 streamlit 可视化
依赖：
    pip install simpy
"""
import random
import simpy


# ============================================================
# 工厂类型库（可配置）：不同性质工厂的工艺拓扑/设备/设计产能/数字孪生建模重点
# ------------------------------------------------------------
# 每种工厂用自己的 stations 拓扑，仿真引擎按 factory_type 驱动；
# 下游"总线→落库→回查"与场景逻辑不变，仅数据源（工位定义）替换为对应类型。
# 正式落地时把这里替换为真实工厂的 BOP（工艺路线）/布局数据即可。
# ============================================================
FACTORY_LIBRARY = {
    "machining": {
        "display": "机加工工厂",
        "desc": "多品种小批量金属零件加工，典型工艺：下料→粗加工→精加工→热处理→检测。",
        "stations": [
            ("下料", 0.9, 0.15, 2),
            ("CNC粗加工", 2.4, 0.40, 3),
            ("CNC精加工", 1.8, 0.35, 3),
            ("热处理", 1.5, 0.30, 2),
            ("三坐标检测", 1.2, 0.25, 2),
        ],
        "new_plant": {"arrival_interval": 0.88, "designed_capacity_per_h": 70.0},
        "existing_plant": {"arrival_interval": 0.71, "add_machines": 1},
        "dt_focus": "以单台 CNC/热处理设备为孪生体，重点建模刀具寿命、换型(set-up)时间与在制品(WIP)队列；几何精度需达 ≤0.5mm 以匹配加工公差。",
        "pain_points": [
            "多品种小批量换型频繁，set-up 损失占比高",
            "刀具磨损导致质量漂移，缺乏寿命预测",
            "工序间在制品积压，齐套率低",
        ],
        "recommend": "场景①验证产能可达性与换型节拍；场景②对 CNC粗加工/热处理增资，推演产能爬坡与瓶颈转移。",
    },
    "assembly": {
        "display": "装备装配工厂",
        "desc": "大型装备/机电设备总装，典型工艺：部装→总装→线缆敷设→调试→出厂检验，节拍长、周期大。",
        "stations": [
            ("部装", 2.5, 0.40, 2),
            ("总装", 3.2, 0.60, 3),
            ("线缆敷设", 2.0, 0.35, 2),
            ("调试", 4.5, 0.70, 2),
            ("出厂检验", 1.5, 0.30, 2),
        ],
        "new_plant": {"arrival_interval": 2.50, "designed_capacity_per_h": 25.0},
        "existing_plant": {"arrival_interval": 2.00, "add_machines": 1},
        "dt_focus": "以装配工位+物料齐套状态为孪生核心，建模 BOM 齐套、调试返工回路；长周期装配需工序级时间孪生。",
        "pain_points": [
            "物料齐套难，缺料导致长周期停等",
            "调试返工率高，节拍不稳定",
            "大型装备占用场地大，布局物流敏感",
        ],
        "recommend": "场景①验证总装线平衡与齐套节奏；场景②对调试工位增资，推演长周期产能爬坡。",
    },
    "semiconductor": {
        "display": "半导体工厂",
        "desc": "晶圆制造(Fab)，典型工艺：光刻→刻蚀→薄膜沉积→离子注入→CMP→检测，设备极昂贵、重入式工艺。",
        "stations": [
            ("光刻", 5.0, 0.80, 2),
            ("刻蚀", 3.0, 0.50, 3),
            ("薄膜沉积", 3.5, 0.60, 3),
            ("离子注入", 2.5, 0.40, 2),
            ("CMP", 2.8, 0.45, 2),
            ("检测", 2.0, 0.30, 3),
        ],
        "new_plant": {"arrival_interval": 2.79, "designed_capacity_per_h": 22.0},
        "existing_plant": {"arrival_interval": 1.50, "add_machines": 1},
        "dt_focus": "以昂贵机台(光刻/刻蚀)为孪生体，建模 OEE、重入式工艺回路与良率(yield)；设备级孪生需对接 SECS/GEM 实时数据。",
        "pain_points": [
            "光刻机等设备单台价值亿级，OEE 提升 1% 即巨额收益",
            "重入式工艺，同一 wafer 多次经过同机台，排程复杂",
            "良率波动溯源难，需工艺-设备联合孪生",
        ],
        "recommend": "场景①验证机台布局与产能可达性；场景②对光刻机台增资，推演瓶颈缓解与回报。",
    },
    "automotive": {
        "display": "汽车流水线",
        "desc": "整车总装流水线，典型工艺：冲压→焊装→涂装→总装→质检，刚性节拍、混线生产。",
        "stations": [
            ("冲压", 1.0, 0.15, 4),
            ("焊装", 2.2, 0.30, 6),
            ("涂装", 2.8, 0.40, 4),
            ("总装", 3.2, 0.40, 6),
            ("质检", 1.5, 0.25, 4),
        ],
        "new_plant": {"arrival_interval": 0.77, "designed_capacity_per_h": 80.0},
        "existing_plant": {"arrival_interval": 0.55, "add_machines": 1},
        "dt_focus": "以节拍(takt)为孪生主线，建模混线车型切换、停线损失(OEE)与缓冲区策略；整线级孪生需对接 ANDON/PLC。",
        "pain_points": [
            "刚性节拍，任一工位停线即拖累整线",
            "多车型混线，换型与排序复杂",
            "涂装等高污染高能耗工段，能耗与节拍耦合",
        ],
        "recommend": "场景①验证 JPH(辆/时)可达性与线平衡；场景②对涂装/总装增资，推演节拍释放。",
    },
    "electronics": {
        "display": "电子组装工厂",
        "desc": "消费电子/SMT 组装，典型工艺：SMT贴片→DIP插件→回流焊→组装→ICT测试→包装，多品种、节拍快、测试敏感。",
        "stations": [
            ("SMT贴片", 0.6, 0.10, 4),
            ("DIP插件", 1.2, 0.20, 3),
            ("回流焊", 0.8, 0.12, 2),
            ("组装", 1.0, 0.18, 3),
            ("ICT测试", 1.5, 0.25, 2),
            ("包装", 0.7, 0.12, 2),
        ],
        "new_plant": {"arrival_interval": 0.90, "designed_capacity_per_h": 70.0},
        "existing_plant": {"arrival_interval": 0.55, "add_machines": 1},
        "dt_focus": "以 SMT 产线 + ICT 测试工站为孪生核心，建模贴片节拍、抛料率、测试良率；SMT 数字孪生需对接 SPI/AOI/ICT 实时数据。",
        "pain_points": [
            "SMT 换线频繁，贴片程序与钢网准备时间长",
            "ICT/功能测试是典型瓶颈，测试工装切换慢",
            "多品种小批量，齐套与排产复杂",
        ],
        "recommend": "场景①验证线平衡与可达产能；场景②对 ICT 测试工位增资，推演瓶颈缓解与产能爬坡。",
    },
}

FACTORY_ORDER = ["machining", "assembly", "semiconductor", "automotive", "electronics"]


def list_factories():
    """返回 [(key, 显示名), ...]，供 UI 下拉/单选使用。"""
    return [(k, FACTORY_LIBRARY[k]["display"]) for k in FACTORY_ORDER]


def get_factory_spec(factory_type):
    """返回某工厂类型的完整配置 dict（含 stations / 场景参数 / 方案要点）。"""
    return FACTORY_LIBRARY[factory_type]


class Station:
    """一个工位（工作站）：含机器数（资源容量）与加工时间分布（分钟）。"""

    def __init__(self, env, name, proc_mean, proc_std, machines):
        self.env = env
        self.name = name
        self.proc_mean = proc_mean
        self.proc_std = proc_std
        self.resource = simpy.Resource(env, capacity=machines)
        self.busy = 0.0        # 累计繁忙时长（多机器累加）
        self.processed = 0     # 处理零件数


def _part_flow(env, stations, results):
    """一个零件依次流经所有工位的离散事件过程。"""
    t_arrive = env.now
    for st in stations:
        with st.resource.request() as req:
            yield req
            proc = max(0.02, random.gauss(st.proc_mean, st.proc_std))
            yield env.timeout(proc)
            st.busy += proc
            st.processed += 1
    results["completed"] += 1
    results["cycle_times"].append(env.now - t_arrive)


def _runner(stations_spec, arrival_interval, sim_minutes, seed=42):
    """构建并运行一次仿真，返回 (env, stations, results)。"""
    random.seed(seed)
    env = simpy.Environment()
    stations = [Station(env, n, m, s, c) for (n, m, s, c) in stations_spec]
    results = {"completed": 0, "cycle_times": []}

    def generator():
        while env.now < sim_minutes:
            yield env.timeout(random.expovariate(1.0 / arrival_interval))
            env.process(_part_flow(env, stations, results))

    env.process(generator())
    env.run(until=sim_minutes)
    return env, stations, results


def _summarize(env, stations, results, designed_capacity_per_h=None):
    sim_min = env.now
    n = len(stations)
    # 关键点：busy 是多机器繁忙累加，利用率须除以 (时长 × 机器数)，否则会 >1
    utils = [st.busy / (sim_min * st.resource.capacity) for st in stations]
    throughput_per_h = results["completed"] / sim_min * 60.0
    avg_cycle = (sum(results["cycle_times"]) / len(results["cycle_times"])) if results["cycle_times"] else 0.0
    b_idx = max(range(n), key=lambda i: utils[i])
    total_mean = sum(st.proc_mean for st in stations)
    max_mean = max(st.proc_mean for st in stations)
    line_balance = (1 - max_mean / total_mean) if total_mean > 0 else 0.0
    out = {
        "sim_minutes": round(sim_min, 1),
        "throughput_per_h": round(throughput_per_h, 2),
        "avg_cycle_time_min": round(avg_cycle, 2),
        "station_util": {st.name: round(u, 3) for st, u in zip(stations, utils)},
        "bottleneck": stations[b_idx].name,
        "bottleneck_util": round(utils[b_idx], 3),
        "line_balance_rate": round(line_balance, 3),
    }
    if designed_capacity_per_h:
        out["designed_capacity_per_h"] = designed_capacity_per_h
        out["reachability"] = round(min(throughput_per_h / designed_capacity_per_h, 1.5), 3)
    return out


# ------------------------------------------------------------------
# 场景① 新建工厂虚拟验证
# ------------------------------------------------------------------
def simulate_new_plant(
    factory_type="machining",
    stations_spec=None,
    arrival_interval=None,       # 到达间隔（分钟）；默认取工厂库 new_plant 配置
    sim_minutes=28800.0,         # ≈ 480 小时连续生产（演示压缩）
    designed_capacity_per_h=None,  # 设计产能（件/小时）；默认取工厂库配置
    seed=42,
):
    """
    新建厂虚拟验证：给定产线布局（工位/机器数/节拍），在动工前仿真验证
    产能可达性、产线平衡率、瓶颈工位。
    按 factory_type 从工厂库取对应工艺拓扑；也可显式传 stations_spec 覆盖。
    """
    if stations_spec is None:
        stations_spec = FACTORY_LIBRARY[factory_type]["stations"]
    if arrival_interval is None:
        arrival_interval = FACTORY_LIBRARY[factory_type]["new_plant"]["arrival_interval"]
    if designed_capacity_per_h is None:
        designed_capacity_per_h = FACTORY_LIBRARY[factory_type]["new_plant"]["designed_capacity_per_h"]
    env, stations, results = _runner(stations_spec, arrival_interval, sim_minutes, seed)
    return _summarize(env, stations, results, designed_capacity_per_h)


# ------------------------------------------------------------------
# 场景② 存量工厂产能优化
# ------------------------------------------------------------------
def simulate_existing_plant_optimization(
    factory_type="machining",
    stations_spec=None,
    arrival_interval=None,       # 到达间隔（分钟）；默认取工厂库 existing_plant 配置
    sim_minutes=1440.0,          # 存量扩产场景：到达率高于瓶颈产能，用 24h 压缩仿真控制队列膨胀
    add_machines=None,           # 对瓶颈工位追加的机器数；默认取工厂库配置
    seed=42,
):
    """
    存量产能优化：先跑现状得 baseline（瓶颈诊断），再对瓶颈工位增资 add_machines
    台机器，重跑得 optimized，输出爬坡比例与瓶颈是否转移。按 factory_type 取拓扑。
    """
    if stations_spec is None:
        stations_spec = FACTORY_LIBRARY[factory_type]["stations"]
    if arrival_interval is None:
        arrival_interval = FACTORY_LIBRARY[factory_type]["existing_plant"]["arrival_interval"]
    if add_machines is None:
        add_machines = FACTORY_LIBRARY[factory_type]["existing_plant"]["add_machines"]
    # baseline
    env0, st0, r0 = _runner(stations_spec, arrival_interval, sim_minutes, seed)
    base = _summarize(env0, st0, r0)
    # 优化：瓶颈工位 +add_machines（利用率分母修正后瓶颈判断才正确）
    b_idx = max(range(len(st0)), key=lambda i: st0[i].busy / (env0.now * st0[i].resource.capacity))
    opt_spec = list(stations_spec)
    name, m, s, c = opt_spec[b_idx]
    opt_spec[b_idx] = (name, m, s, c + add_machines)
    env1, st1, r1 = _runner(opt_spec, arrival_interval, sim_minutes, seed)
    opt = _summarize(env1, st1, r1)
    uplift = (opt["throughput_per_h"] - base["throughput_per_h"]) / base["throughput_per_h"]
    return {
        "baseline": base,
        "optimized": opt,
        "bottleneck_station": base["bottleneck"],
        "added_machines": add_machines,
        "throughput_uplift": round(uplift, 3),
        "bottleneck_shifted": base["bottleneck"] != opt["bottleneck"],
        "new_bottleneck": opt["bottleneck"],
    }


def run_demo():
    print("工厂类型库覆盖：", "、".join(FACTORY_LIBRARY[k]["display"] for k in FACTORY_ORDER))
    print()
    for ft in FACTORY_ORDER:
        spec = FACTORY_LIBRARY[ft]
        print("=" * 64)
        print(f"【{spec['display']}】{spec['desc']}")
        print("=" * 64)
        r1 = simulate_new_plant(factory_type=ft)
        print("  场景① 新建厂虚拟验证：")
        print(f"    产能={r1['throughput_per_h']} 件/时  设计产能可达性={r1.get('reachability', 0)*100:.1f}%  "
              f"线平衡率={r1['line_balance_rate']*100:.1f}%  瓶颈={r1['bottleneck']}({r1['bottleneck_util']*100:.1f}%)")
        r2 = simulate_existing_plant_optimization(factory_type=ft)
        print("  场景② 存量产能优化：")
        print(f"    现状产能={r2['baseline']['throughput_per_h']} 件/时 → 优化后={r2['optimized']['throughput_per_h']} 件/时  "
              f"爬坡={r2['throughput_uplift']*100:.1f}%  瓶颈{'转移→'+r2['new_bottleneck'] if r2['bottleneck_shifted'] else '未转移'}")
        print(f"    数字孪生建模重点：{spec['dt_focus']}")
        print()
    print("FACTORY_SIM_OK")


if __name__ == "__main__":
    run_demo()
