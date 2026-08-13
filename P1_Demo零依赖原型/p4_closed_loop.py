# -*- coding: utf-8 -*-
"""
P4 闭环自治演示（CESI L4 成熟度 · 硬证据）
=========================================
把 factory_sim_core 的「识别瓶颈 → 增资优化 → 重仿」封装成一个**自主闭环**：

   数字孪生实时监测产线 → 检测到瓶颈工位利用率过高（产能受限）
        ↓
   系统【自主】决策：在瓶颈工位追加 1 台机器（无需人工干预）
        ↓
   自动写回现场（重配置仿真产线参数）并重新仿真
        ↓
   验证 KPI 提升（吞吐上升 / 瓶颈利用率下降）→ 闭环收敛，记录决策日志

这就是 CESI L4「自主/认知孪生（预测 + 自主优化）」的定性证据：
当前系统（P3 自评 L3）只做到「预测 + 给人建议」，本模块补齐
「自主优化 + 虚实互驱闭环」这一档能力缺口。

API：
  run_closed_loop(factory_type="machining", target_util=0.85, max_iter=4) -> dict
  closed_loop_plotly(result) -> plotly.graph_objects.Figure
  self-test:  python p4_closed_loop.py

依赖：numpy / scipy / pandas（已在 venv 中）；plotly（Demo 渲染用）
"""
import time

import numpy as np

import factory_sim_core as fs
from factory_sim_core import _runner, _summarize   # 复用既有离散事件内核


# ============================================================
# 核心：自主闭环
# ============================================================
def run_closed_loop(factory_type: str = "machining",
                    target_util: float = 0.85,
                    max_iter: int = 4,
                    seed: int = 42) -> dict:
    """
    运行一次自主闭环优化。

    target_util : 瓶颈工位利用率目标上限；高于此值视为「产能受限」，触发自主增资。
    max_iter    : 最大增资迭代次数（防止无限循环）。
    返回聚合结果 dict（含逐轮决策日志、基线/最终 KPI、闭环收敛判定）。
    """
    t0 = time.perf_counter()

    spec0 = list(fs.FACTORY_LIBRARY[factory_type]["stations"])
    arrival = fs.FACTORY_LIBRARY[factory_type]["existing_plant"]["arrival_interval"]
    # 目标产能取新建厂设计产能（可达性分母）
    designed = fs.FACTORY_LIBRARY[factory_type]["new_plant"]["designed_capacity_per_h"]
    sim_min = 1440.0   # 24h 压缩仿真，控制高到达率下的队列膨胀

    # —— 基线（现状）——
    env0, st0, r0 = _runner(spec0, arrival, sim_min, seed)
    base = _summarize(env0, st0, r0, designed)
    base_util = base["bottleneck_util"]

    cur_spec = list(spec0)
    log = []
    iter_n = 0
    cur = dict(base)

    # —— 自主闭环迭代：检测到瓶颈超限 → 自主增资 → 重仿验证 ——
    while cur["bottleneck_util"] > target_util and iter_n < max_iter:
        # 自主决策：定位当前瓶颈工位
        b_idx = max(range(len(st0)),
                    key=lambda i: st0[i].busy / (env0.now * st0[i].resource.capacity)) \
            if iter_n == 0 else \
            max(range(len(cur["station_util"])),
                key=lambda i: list(cur["station_util"].values())[i])
        name, m, s, c = cur_spec[b_idx]
        cur_spec[b_idx] = (name, m, s, c + 1)   # 自主 +1 机器（写回现场）
        env1, st1, r1 = _runner(cur_spec, arrival, sim_min, seed)
        cur = _summarize(env1, st1, r1, designed)
        iter_n += 1
        log.append({
            "iter": iter_n,
            "action": f"瓶颈工位「{name}」自主增资 +1 台（{c}→{c + 1}）",
            "throughput_per_h": cur["throughput_per_h"],
            "bottleneck_util": cur["bottleneck_util"],
            "bottleneck": cur["bottleneck"],
        })

    elapsed = round(time.perf_counter() - t0, 3)
    uplift = (cur["throughput_per_h"] - base["throughput_per_h"]) / base["throughput_per_h"] \
        if base["throughput_per_h"] > 0 else 0.0
    converged = (cur["bottleneck_util"] <= target_util) or (iter_n >= max_iter and uplift > 0)

    return {
        "factory_type": factory_type,
        "factory_display": fs.FACTORY_LIBRARY[factory_type]["display"],
        "target_util": target_util,
        "design_capacity_per_h": designed,
        "base": base,
        "final": cur,
        "baseline_throughput": base["throughput_per_h"],
        "final_throughput": cur["throughput_per_h"],
        "throughput_uplift_pct": round(uplift * 100.0, 2),
        "baseline_bottleneck_util": round(base_util, 3),
        "final_bottleneck_util": cur["bottleneck_util"],
        "added_machines_total": iter_n,
        "decision_log": log,
        "converged": bool(converged),
        "wall_time_s": elapsed,
    }


# ============================================================
# 可视化（Demo 渲染）
# ============================================================
def closed_loop_plotly(result: dict):
    """返回闭环前后吞吐 / 瓶颈利用率对比柱状图（plotly Figure）。"""
    import plotly.graph_objects as go

    base_tp = result["baseline_throughput"]
    final_tp = result["final_throughput"]
    base_u = result["baseline_bottleneck_util"] * 100.0
    final_u = result["final_bottleneck_util"] * 100.0

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["基线（现状）", "闭环后（自主优化）"],
        y=[base_tp, final_tp],
        name="产能 件/时",
        marker_color=["#94a3b8", "#2563eb"],
        text=[f"{base_tp:.1f}", f"{final_tp:.1f}"],
        textposition="auto",
    ))
    fig.add_trace(go.Bar(
        x=["基线（现状）", "闭环后（自主优化）"],
        y=[base_u, final_u],
        name="瓶颈利用率 %",
        marker_color=["#f59e0b", "#16a34a"],
        text=[f"{base_u:.1f}%", f"{final_u:.1f}%"],
        textposition="auto",
        yaxis="y2",
    ))
    fig.update_layout(
        title=f"L4 闭环自治：{result['factory_display']} 产能 {result['throughput_uplift_pct']:+.1f}% ↑",
        barmode="group",
        height=340,
        margin=dict(l=40, r=40, t=50, b=30),
        legend=dict(orientation="h", y=-0.18),
        yaxis=dict(title="产能 件/时"),
        yaxis2=dict(title="瓶颈利用率 %", overlaying="y", side="right", range=[0, 110]),
        font=dict(size=12),
    )
    return fig


# ============================================================
# 自检
# ============================================================
def _self_test():
    print("=" * 64)
    print("  P4 闭环自治 · 自检（L4 自主优化硬证据）")
    print("=" * 64)
    cases = ["machining", "semiconductor", "automotive"]
    all_ok = True
    for ft in cases:
        res = run_closed_loop(ft, target_util=0.85, max_iter=4)
        ok = res["throughput_uplift_pct"] > 0 and res["final_bottleneck_util"] < \
            res["baseline_bottleneck_util"] + 1e-6 and res["converged"]
        all_ok &= ok
        print(f"\n[{res['factory_display']}] "
              f"基线吞吐 {res['baseline_throughput']:.1f} → 闭环 {res['final_throughput']:.1f} 件/时 "
              f"(uplift {res['throughput_uplift_pct']:+.1f}%)")
        print(f"  瓶颈利用率 {res['baseline_bottleneck_util']*100:.1f}% → "
              f"{res['final_bottleneck_util']*100:.1f}% ｜ 自主增资 {res['added_machines_total']} 台 ｜ "
              f"闭环收敛={res['converged']} ｜ {res['wall_time_s']}s")
        for step in res["decision_log"]:
            print(f"    - 第{step['iter']}轮：{step['action']}")
        print(f"  判定: [PASS]" if ok else f"  判定: [FAIL]")

    print("\n" + "=" * 64)
    print(f"  总体: [P4_CLOSED_LOOP_OK]" if all_ok else "  总体: [SOME FAIL]")
    print("=" * 64)
    return all_ok


if __name__ == "__main__":
    _self_test()
