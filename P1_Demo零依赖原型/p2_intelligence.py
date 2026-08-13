# -*- coding: utf-8 -*-
"""
P2 智能保真层 · 解耦 Agent 智能层（通用 MAS 接口）
================================================
构件 E（P2 启动包）：把"诊断 / 预测 / 决策"三类 Agent 以厂商无关的统一契约接入，
对外暴露 输入(仿真+实时数据) → 输出(诊断结论/预测值/决策建议)。

设计原则（延续 P1「降依赖、先把 Demo 跑起来」）：
  • 规则引擎兜底：无大模型也能跑通闭环（已验证优雅降级）。
  • 可选本地 LLM：Ollama + DeepSeek/GLM 量化版占位，数据不出域；未装则自动降级。
  • 指标埋点：采集 诊断准确率 / 预测精度(R²) / 决策一致性，为 P3 可信性测评预存数据，
    对应 GB/T 45626：故障诊断 6.4 / 状态预测 6.5 / 连接交互 7.4。
  • 当前为演示级埋点框架（真值来自工况注入），重型评测在 P3 完成。

运行：python p2_intelligence.py   # 跑一个闭环演示
依赖：numpy（已在 venv 中）
"""
import random
import numpy as np

# 可选的本地 LLM（Ollama），未就绪则 HAS_OLLAMA=False，自动走规则兜底
HAS_OLLAMA = False
try:
    import ollama
    HAS_OLLAMA = True
except Exception:  # noqa
    HAS_OLLAMA = False


# ============================================================
# 通用 MAS 接口契约（厂商无关，按指标选型，与规划方案一致）
# ============================================================
class DiagnosticAgent:
    """诊断智能体：异常检测 + 根因分析（GB/T 45626 故障诊断 6.4）。"""
    def diagnose(self, sensor: dict) -> dict:
        raise NotImplementedError


class PredictiveAgent:
    """预测智能体：趋势预报 + 剩余寿命(RUL)估算（GB/T 45626 状态预测 6.5）。"""
    def predict(self, series) -> dict:
        raise NotImplementedError


class DecisionAgent:
    """决策智能体：反馈控制 / 优化建议（GB/T 45626 连接交互 7.4）。"""
    def decide(self, context: dict) -> dict:
        raise NotImplementedError


# ============================================================
# 规则引擎实现（零依赖兜底，保证闭环不断链）
# ============================================================
class RuleDiagnostic(DiagnosticAgent):
    def diagnose(self, sensor: dict) -> dict:
        alerts, sev = [], "normal"
        if sensor.get("temp", 0) > 55:
            alerts.append("高温告警：疑似散热异常，检查冷却回路")
            sev = "high"
        if sensor.get("vib", 0) > 1.5:
            alerts.append("振动突增：轴承磨损风险上升，建议润滑/换型")
            sev = "high"
        # 注意：severity 为等级量，不能用 max() 做字符串比较（'m'>'h'），
        # 转速下降仅在未达 high 时记为 mid。
        if sensor.get("rpm", 0) < 1450 and sev != "high":
            alerts.append("转速下降：排查负载突变或供电波动")
            sev = "mid"
        return {"source": "rule", "alerts": alerts, "severity": sev,
                "summary": "；".join(alerts) if alerts else "工况正常"}


class RulePredictive(PredictiveAgent):
    """对历史序列做线性回归外推，R² 作趋势可解释度；样本外滚动 MAPE 作预测精度；
    按趋势估算剩余寿命(RUL)。"""
    def predict(self, series, horizon=10, threshold=2.5):
        if series is None or len(series) < 6:
            return {"available": False}
        x = np.arange(len(series), dtype=float)
        y = np.array(series, dtype=float)
        A = np.polyfit(x, y, 1)          # [斜率, 截距]
        yhat = np.polyval(A, x)
        ss_res = float(np.sum((y - yhat) ** 2))
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-9 else 0.0
        slope = float(A[0])
        # 样本外滚动 MAPE：用前 w 点线性外推预测下一点，与实际比（预测精度指标）
        mape = None
        w = 8
        if len(y) > w + 3:
            errs = []
            for i in range(w, len(y)):
                seg = y[i - w:i]
                Aw = np.polyfit(np.arange(w, dtype=float), seg, 1)
                pred = np.polyval(Aw, w)
                if y[i] != 0:
                    errs.append(abs((y[i] - pred) / y[i]))
            mape = float(np.mean(errs)) * 100 if errs else None
        # RUL：若趋势上升且趋向阈值，估算到阈值的剩余步数（演示级）
        rul = None
        if slope > 1e-4 and threshold > y[-1]:
            rul = int((threshold - y[-1]) / slope)
        # 未来 horizon 步外推
        xf = np.arange(len(series), len(series) + horizon, dtype=float)
        forecast = np.polyval(A, xf).tolist()
        return {
            "available": True,
            "r2": round(r2, 3),
            "mape_pct": round(mape, 2) if mape is not None else None,
            "slope": round(slope, 5),
            "forecast": [round(v, 2) for v in forecast],
            "rul_steps": rul,
            "trend": "上升" if slope > 1e-4 else ("下降" if slope < -1e-4 else "平稳"),
        }


class RuleDecision(DecisionAgent):
    def decide(self, context: dict) -> dict:
        diag = context.get("diagnostic", {})
        pred = context.get("predictive", {})
        sim = context.get("sim", {})
        recs, params, conf = [], {}, 0.9
        if diag.get("severity") == "high":
            recs.append("立即停机巡检：优先排查轴承磨损与散热回路")
            conf = 0.95
        if pred.get("rul_steps") is not None and pred["rul_steps"] < 240:  # < ~4h(步)
            recs.append(f"未来 {pred['rul_steps']} 个采样周期内安排预测性维护")
        # 产能可达性反馈（连接交互 7.4）：若优化后可达性偏低，建议对瓶颈增资
        reach = sim.get("reachability") if isinstance(sim, dict) else None
        if reach is not None and reach < 0.9:
            recs.append(f"产能可达性仅 {reach*100:.0f}%，建议对瓶颈工位预留扩产余量")
        if not recs:
            recs.append("维持当前工艺参数，持续监测")
        return {"recommendations": recs, "params": params,
                "confidence": conf, "summary": "；".join(recs)}


# ============================================================
# 可选本地 LLM 智能体（Ollama 占位，未就绪自动降级）
# ============================================================
class LocalLLMDiagnostic(DiagnosticAgent):
    def __init__(self, model="deepseek-r1:7b"):
        self.model = model

    def diagnose(self, sensor: dict) -> dict:
        if not HAS_OLLAMA:
            return {"source": "llm-unavailable",
                    "note": "ollama 未就绪，已自动降级规则引擎", "alerts": []}
        prompt = (f"你是工业设备诊断专家。温度{sensor['temp']}°C，振动{sensor['vib']}mm/s，"
                  f"转速{sensor['rpm']}rpm。给出故障结论与维护建议，分点简洁中文。")
        try:
            r = ollama.generate(model=self.model, prompt=prompt)
            return {"source": "llm", "diagnosis": r["response"], "alerts": []}
        except Exception as e:  # noqa
            return {"source": "llm-error", "error": str(e), "alerts": []}


# ============================================================
# 可信性指标埋点（为 P3 测评预存；演示级，真值来自工况注入）
# ============================================================
_METRICS = {
    "tp": 0, "fp": 0, "tn": 0, "fn": 0,   # 诊断混淆矩阵
    "r2_sum": 0.0, "r2_n": 0,              # 预测精度累计
    "decision_log": [],                    # 决策一致性样本
}


def _ground_truth_fault(sensor: dict) -> bool:
    """演示级真值：温度>54 或 振动>1.5 视为真实故障工况（与阈值一致，便于演示）。"""
    return sensor.get("temp", 0) > 54 or sensor.get("vib", 0) > 1.5


def update_metrics(diagnosis: dict, sensor: dict, predictive: dict, decision: dict):
    """每轮调用，累积可信性指标。"""
    gt = _ground_truth_fault(sensor)
    pred_fault = diagnosis.get("severity") == "high"
    if gt and pred_fault:
        _METRICS["tp"] += 1
    elif (not gt) and pred_fault:
        _METRICS["fp"] += 1
    elif gt and (not pred_fault):
        _METRICS["fn"] += 1
    else:
        _METRICS["tn"] += 1
    if predictive.get("available") and "r2" in predictive:
        _METRICS["r2_sum"] += predictive["r2"]
        _METRICS["r2_n"] += 1
    _METRICS["decision_log"].append(decision.get("summary", ""))
    if len(_METRICS["decision_log"]) > 50:
        _METRICS["decision_log"].pop(0)


def get_metrics() -> dict:
    tp, fp, tn, fn = (_METRICS[k] for k in ("tp", "fp", "tn", "fn"))
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    acc = (tp + tn) / (tp + fp + tn + fn) if (tp + fp + tn + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    r2_avg = _METRICS["r2_sum"] / _METRICS["r2_n"] if _METRICS["r2_n"] else 0.0
    # 决策一致性：相同建议占比（规则确定性高 → 接近 100%）
    log = _METRICS["decision_log"]
    consistency = 1.0
    if len(log) > 1:
        from collections import Counter
        c = Counter(log)
        consistency = c.most_common(1)[0][1] / len(log)
    return {
        "diagnostic_accuracy": round(acc, 3),
        "diagnostic_precision": round(prec, 3),
        "diagnostic_recall": round(rec, 3),
        "diagnostic_f1": round(f1, 3),
        "predictive_r2_avg": round(r2_avg, 3),
        "decision_consistency": round(consistency, 3),
        "samples": tp + fp + tn + fn,
    }


# ============================================================
# 统一入口：三类 Agent 闭环（接入仿真 + 实时传感）
# ============================================================
def run_intelligence_layer(latest_sensor: dict, temp_hist, vib_hist, sim_context: dict):
    """运行诊断/预测/决策三类 Agent，更新并返回指标埋点。
    latest_sensor: 最新传感器读数 {temp,vib,rpm}
    temp_hist/vib_hist: 历史序列（list/array），用于预测外推
    sim_context: 工厂仿真结果 dict（含 reachability 等），用于决策反馈
    """
    diag = RuleDiagnostic().diagnose(latest_sensor)
    pred = RulePredictive().predict(list(temp_hist) if temp_hist is not None else None)
    ctx = {"diagnostic": diag, "predictive": pred, "sim": sim_context or {}}
    dec = RuleDecision().decide(ctx)
    update_metrics(diag, latest_sensor, pred, dec)
    metrics = get_metrics()
    return {"diagnostic": diag, "predictive": pred, "decision": dec, "metrics": metrics}


# ============================================================
# 演示
# ============================================================
def run_demo():
    print("智能保真层 · 三类 Agent 闭环演示（规则引擎兜底）")
    print(f"  本地 LLM 可用: {HAS_OLLAMA}\n")
    for i in range(6):
        abnormal = (i % 3 == 0)
        sensor = {
            "temp": random.uniform(58, 65) if abnormal else random.uniform(42, 50),
            "vib": random.uniform(1.8, 2.4) if abnormal else random.uniform(0.6, 1.1),
            "rpm": random.randint(1380, 1440) if abnormal else random.randint(1480, 1520),
        }
        temp_hist = [random.uniform(43, 48) + 0.02 * j for j in range(20)]
        sim_ctx = {"reachability": 0.999 if i % 2 else 0.85}
        out = run_intelligence_layer(sensor, temp_hist, temp_hist, sim_ctx)
        print(f"[轮 {i}] 工况={'异常' if abnormal else '正常'}")
        print(f"  诊断: {out['diagnostic']['summary']} (severity={out['diagnostic']['severity']})")
        if out["predictive"].get("available"):
            pv = out["predictive"]
            print(f"  预测: R²={pv['r2']} MAPE={pv['mape_pct']}% 趋势={pv['trend']} "
                  f"RUL步={pv['rul_steps']}")
        print(f"  决策: {out['decision']['summary']}")
        print(f"  指标: 诊断准确率={out['metrics']['diagnostic_accuracy']} "
              f"预测R²={out['metrics']['predictive_r2_avg']} "
              f"决策一致性={out['metrics']['decision_consistency']}\n")
    print("P2_INTELLIGENCE_OK")


if __name__ == "__main__":
    run_demo()
