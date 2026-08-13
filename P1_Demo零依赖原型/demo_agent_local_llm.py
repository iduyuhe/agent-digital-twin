"""
智能保真层 · 本地 LLM（Ollama）+ 通用 MAS 接口原型
====================================================
正式路径：Agent 层用通用 MAS（多智能体系统）接口，本地 LLM 用 Ollama 跑
          DeepSeek / GLM 量化版（数据不出域、免云、免 GPU 大模型 API）。
演示：传感器数据 → 规则初步判断 → LLM 深度诊断 → 结构化结论。

降级路径：无 ollama 服务/未装时，自动 fallback 到规则引擎，保证 Demo 可跑。

依赖（正式）：
    pip install ollama
    # 本地需先：ollama serve   &&   ollama pull deepseek-r1:7b
运行：
    python demo_agent_local_llm.py
"""
import sys
import random

HAS_OLLAMA = False
try:
    import ollama
    HAS_OLLAMA = True
except Exception:  # noqa
    HAS_OLLAMA = False


# ---------- 通用 MAS 接口契约（厂商无关、按指标选型，与规划方案一致）----------
class DiagnosticAgent:
    """所有诊断智能体统一接口——解耦具体 LLM / 规则实现。"""
    def diagnose(self, sensor: dict) -> dict:
        raise NotImplementedError


class RuleAgent(DiagnosticAgent):
    """规则引擎：阈值告警（Demo 占位智能层）。"""
    def diagnose(self, sensor: dict) -> dict:
        alerts = []
        if sensor["temp"] > 55:
            alerts.append("高温告警：疑似散热异常")
        if sensor["vib"] > 1.5:
            alerts.append("振动突增：预测轴承磨损风险↑")
        if sensor["rpm"] < 1450:
            alerts.append("转速下降：排查负载/供电")
        return {
            "source": "rule",
            "alerts": alerts,
            "severity": "high" if alerts else "normal",
        }


class LocalLLMAgent(DiagnosticAgent):
    """本地 LLM 智能体：Ollama 接入，通用 MAS 接口实现。"""
    def __init__(self, model: str = "deepseek-r1:7b"):
        self.model = model

    def diagnose(self, sensor: dict) -> dict:
        if not HAS_OLLAMA:
            return {
                "source": "llm-unavailable",
                "note": "ollama 未就绪：请先 `ollama serve` 并 `ollama pull %s`" % self.model,
                "alerts": [],
            }
        prompt = (
            "你是一名工业设备诊断专家。当前传感器数据：\n"
            f"- 温度：{sensor['temp']} °C\n"
            f"- 振动：{sensor['vib']} mm/s\n"
            f"- 转速：{sensor['rpm']} rpm\n"
            "请判断设备健康状态，给出故障诊断结论与维护建议，用简洁中文分点回答。"
        )
        try:
            r = ollama.generate(model=self.model, prompt=prompt)
            return {"source": "llm", "diagnosis": r["response"], "alerts": []}
        except Exception as e:  # noqa
            return {"source": "llm-error", "error": str(e), "alerts": []}


def simulate_sensor(abnormal: bool = False) -> dict:
    """模拟一台设备的实时传感器读数。"""
    if abnormal:
        return {"temp": random.uniform(58, 65), "vib": random.uniform(1.8, 2.4), "rpm": random.randint(1380, 1440)}
    return {"temp": random.uniform(42, 50), "vib": random.uniform(0.6, 1.1), "rpm": random.randint(1480, 1520)}


def run_demo():
    rule = RuleAgent()
    llm = LocalLLMAgent()
    sensor = simulate_sensor(abnormal=True)
    print("传感器读数:", {k: round(v, 2) if isinstance(v, float) else v for k, v in sensor.items()})

    r1 = rule.diagnose(sensor)
    print("\n[规则层 / 实时告警]")
    print("  严重度:", r1["severity"])
    for a in r1["alerts"]:
        print("   -", a)

    r2 = llm.diagnose(sensor)
    print("\n[LLM层 / 深度诊断]")
    if r2["source"] == "llm":
        print(r2["diagnosis"])
    else:
        print("  ", r2.get("note") or r2.get("error"))
    print("\nAGENT_OK")


if __name__ == "__main__":
    run_demo()
