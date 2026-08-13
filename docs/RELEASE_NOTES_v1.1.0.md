# 工业智能数字孪生系统 · v1.1.0

> Industrial Intelligent Digital-Twin System — Simulation Fidelity + Intelligence + Integrated Assessment

v1.1.0 是首个包含**完整四期（P0–P3）落地成果**的版本。在 v1.0.0 几何内核 + 数据底座零依赖原型的基础上，新增三大能力域：**工厂级仿真保真标定**、**MAS 智能层（诊断/预测/决策三类 Agent）**、**装备级 CAE 保真（FEM/FDM）**，以及**系统集成测评套件**（GB/T 标准符合性 + CESI 可信性成熟度取证）。

---

## 📋 变更概览

### P2 仿真保真与智能层集成

| 构件 | 内容 | 关键指标 |
|------|------|---------|
| **P2-A1** 工厂仿真保真增强 | 蒙特卡洛 N=24 次标定 vs 解析瓶颈基线；场景②故障/换型/WIP 建模 | 5 类工厂全达标 **≤±0.5%**，CV<1% |
| **P2-A2** 智能层三类 Agent | 诊断 / 预测 / 决策 Agent + 规则引擎兜底 + 可信性指标埋点 | 对标 GB/T 45626（故障诊断 6.4 / 状态预测 6.5） |
| **P2-A3** 统一 Demo 集成 | 新增「智能保真（P2）」模式（4 面板：标定卡 / 场景②增强 / 智能闭环 / 可信性仪表） | Streamlit 实时渲染 |
| **P2-B** 装备级 CAE 保真 | FEM Hermite 梁元 + FDM 热传导求解器 | 5 场景全 PASS **≤±0.004%** |

### P3 集成测评

| 构件 | 内容 | 关键指标 |
|------|------|---------|
| **P3-A** 系统集成测试套件 | 9 项端到端断言（仿真/智能/CAE/数据底座/零依赖） | **100% 通过率** |
| **P3-B** GB/T 标准符合性映射 | GB/T 45626 + 45873-2025 条款逐条对照 | **8/9 条款已实现** |
| **P3-C** CESI 可信性成熟度评分 | 诊断 accuracy/precision/recall/F1 + 预测 R²/MAPE + 决策一致性 | **综合 88/100 → L3 仿真/预测孪生** |
| **P3-D** Demo「集成测评（P3）」模式 | 四面板实时仪表盘（KPI 卡片 / 测试明细 / GB/T 映射 / 成熟度雷达） | 一键运行，结果实时缓存 |

### 文件变更

```
新增文件：
  p2_intelligence.py          # P2 智能层（诊断/预测/决策 三类 Agent）
  p2_cae_fidelity.py          # P2 装备级 CAE 保真（FEM 梁 + FDM 热传导）
  p3_assessment.py            # P3 集成测评（系统测试 + GB/T 符合性 + CESI 成熟度）

修改文件：
  demo_unified.py             # 新增 P2/P3 模式（共 4 种展示模式）
  factory_sim_core.py         # 新增蒙特卡洛标定 + 场景②增强
  README.md                   # 路线图更新（P2→✅, P3→✅），目录树补充

新增资源：
  docs/assets/demo_p3_assessment.png   # P3 集成测评模式截图
```

## 🏗️ 架构

五元架构（物理实体 / 数字实体 / 数据底座 / 智能层 / 应用层）× 双引擎（华为 OGG 几何引擎 + 通用 MAS Agent）。详见 `docs/architecture.svg`。

v1.1.0 在 v1.0.0 的基础上扩展了 **智能层** 和 **集成测评** 两个维度：

```
┌─────────────────────────────────────────────────────┐
│                   应用层                              │
│  demo_unified.py (4 modes: DEMO / 定制 / P2 / P3)    │
├──────────┬──────────┬──────────┬─────────────────────┤
│  智能层  │  仿真保真 │  CAE 保真 │     集成测评        │
│ p2_      │ factory_ │ p2_cae_  │  p3_assessment.py   │
│ intelligence │ _sim_core │ fidelity │                  │
│ (3 Agents)│ (Monte Carlo)│(FEM/FDM)│ (9 tests/GB/T/CESI)│
├──────────┴──────────┴──────────┴─────────────────────┤
│              数据底座 / 几何内核 (P1)                  │
└─────────────────────────────────────────────────────┘
```

## 🚀 快速开始

```bash
# 1. 克隆（二选一）
git clone https://github.com/iduyuhe/agent-digital-twin.git
git clone https://gitee.com/i4hub/agent-digital-twin.git

# 2. 安装依赖
cd agent-digital-twin/P1_Demo零依赖原型
pip install -r requirements.txt   # streamlit / plotly / numpy / pandas / simpy / scipy

# 3. 启动统一 Demo（4 种模式）
python -m streamlit run demo_unified.py --server.port 8505
# 浏览器打开 http://localhost:8505
# 切换到「集成测评（P3）」查看完整的系统评估报告
```

## Demo 截图

<p align="center">
  <img src="docs/assets/demo_p3_assessment.png" alt="P3 集成测评模式截图" width="860"/>
</p>

> 截图展示了 P3 集成测评模式的四大 KPI 卡片：**100% 测试通过率** · **8/9 GB/T 条款符合** · **CESI 综合评分 88** · **L3 成熟度等级**

## 四期建设路线（全部完成 ✅）

- **P0** ✅ 需求规格 / 标准符合性基线 / 评审
- **P1** ✅ 几何内核与数据底座打通（零依赖 Demo + OGG 脚手架）
- **P2** ✅ 仿真保真与智能层集成（蒙特卡洛标定 ±0.5% + 三类 Agent + FEM/FDM CAE）
- **P3** ✅ 系统集成与测评取证（9 项测试 100% + GB/T 8/9 + CESI L3）

## 双平台

- GitHub：https://github.com/iduyuhe/agent-digital-twin/releases/tag/v1.1.0
- Gitee：https://gitee.com/i4hub/agent-digital-twin/releases

## 许可证

[MIT](LICENSE)

---

*从 v1.0.0 到 v1.1.0：零依赖原型 → 仿真保真 → 智能层 → 集成测评，四期路线全线贯通。*
