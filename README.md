<p align="center">
  <img src="docs/architecture.svg" alt="五元架构图" width="920"/>
</p>

<h1 align="center">工业智能数字孪生系统 · 零依赖参考实现</h1>

<p align="center">
  <strong>Industrial Intelligent Digital-Twin — Zero-Dependency Reference Implementation</strong>
</p>

<p align="center">
  <a href="https://github.com/iduyuhe/agent-digital-twin"><img src="https://img.shields.io/badge/GitHub-iduyuhe%2Fagent--digital--twin-181717?style=flat-square&logo=github" alt="GitHub"/></a>
  <a href="https://gitee.com/i4hub/agent-digital-twin"><img src="https://img.shields.io/badge/Gitee-i4hub%2Fagent--digital--twin-C71D23?style=flat-square&logo=gitee" alt="Gitee"/></a>
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"/>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Streamlit-1.61+-FF4B4B?style=flat-square&logo=streamlit" alt="Streamlit"/>
</p>

<p align="center">
  华为 OGG 几何内核 + 通用 MAS Agent 双引擎 · 五元架构 · 四期落地路线（P0–P3）<br/>
  由 <strong>工业5点0产业生态联盟</strong> 开源维护
</p>

---

## ✨ 项目简介

本项目是一套**可本地零依赖运行**的工业智能数字孪生参考实现，目标是把"数字孪生"从 PPT 概念落到可演示、可二次开发的工程骨架：

| 能力域 | 说明 | 本仓库体现 |
|--------|------|-----------|
| 🔷 **几何内核** | 厂房 / 设备 / 产线的三维几何建模 | `P1_W1_开工脚手架/`（OGG 编译与 Docker 化）+ `demo_geometry_occ.py` |
| 📡 **数据底座** | SQLite + 内存队列替代 EMQX+IoTDB，零外部依赖演示完整数据链路 | `demo_databus_sqlite.py`（DataSource 适配层：模拟 / CSV / MES-REST） |
| ⚙️ **离散仿真** | SimPy 产线产能 / 瓶颈 / 可达性仿真，5 类工厂原型 | `factory_sim_core.py` |
| 🤖 **智能规划** | 公司/产品 → 类型判定 → 节拍反算设备数 → 仿真验证，自动生成建设方案 | `planner_core.py` |
| 📊 **集成测评** | 系统级测试、取证、合规验证 | P3 启动包文档 |

整套 Demo **仅需 Python**，无需 Docker、无需联网、无需任何商业中间件即可跑通。

---

## 🎯 核心特性

- **零外部依赖** — 无需 Docker/Kafka/IoTDB，`pip install` 即跑
- **5 类工厂原型** — 机加工 / 装备装配 / 半导体 / 汽车流水线 / 电子组装
- **四模式入口** — 标准 DEMO（标杆参考工厂）+ 客户定制（输入公司/产品自动生成方案）+ 智能保真 P2（仿真标定 + 智能闭环 + CAE 保真）+ 集成测评 P3（系统测试 + GB/T 符合性 + CESI 成熟度）
- **仿真保真标定** — 蒙特卡洛 N=24 次 vs 解析基线，5 类工厂全达标 **≤±0.5%**
- **三类智能 Agent** — 诊断 / 预测 / 决策 Agent，规则引擎兜底 + 可信性指标埋点
- **装备级 CAE 保真** — FEM Hermite 梁元 + FDM 热传导，5 场景全 PASS **≤±0.004%**
- **3D 实体有限元（自研替代商业求解器）** — 二十节点二次六面体 Hex20（对标 ANSYS SOLID186），纯 numpy+scipy 零 license；悬臂梁/轴向拉伸蒙特卡洛标定 **≤1%**，免 ANSYS/Abaqus 依赖
- **动力学求解器（自研替代商业求解器）** — 模态分析（eigsh 广义特征问题）+ 瞬态 Newmark-β 平均加速度法，固有频率对标 Euler-Bernoulli **≤0.8%**、阶跃响应动态放大系数 DAF=1.988（解析 2.000，误差 0.6%），免 ANSYS Modal/Transient 依赖
- **集成测评套件** — 9 项端到端测试 **100% 通过率**，GB/T 8/9 条款符合，CESI 自评 L3（综合 88/100）
- **L4 闭环自治演示（自主优化硬证据）** — `p4_closed_loop`：数字孪生监测瓶颈 → **系统自主**增资 → 重仿验证 → 记录决策日志；机加工 +13% / 半导体 +65% / 汽车 +26% 产能，补 L3→L4 的「虚实互驱闭环」缺口（详见 `docs/CESI_L4_行动方案.md`）
- **客户化规划器** — 输入公司名或产品描述 → 自动判定工厂类型 → 按节拍反算设备 → 生成可下载 HTML 规划书
- **行业模板库** — 5 类工厂可复用规划模板（行业画像/典型产品/典型参数/参考KPI/孪生目标等级），一键套用生成方案，支持 JSON 导出离线复用
- **数据源适配层** — SimulatedSource(默认) / CsvFileSource(MES回放) / MesRestSource(占位)，上线真实系统无缝切换

---

## 🚀 快速开始

### Prerequisites

- **Python 3.10+**（推荐 3.13）

```bash
# 安装依赖
pip install -r P1_Demo零依赖原型/requirements.txt

# 启动统一 Demo（标准DEMO + 客户定制 双模式）
streamlit run P1_Demo零依赖原型/demo_unified.py --server.port 8505
```

浏览器打开 **http://localhost:8505**

> 统一 Demo 顶部可在「**标准DEMO**」「**客户定制**」「**智能保真（P2）**」「**集成测评（P3）**」四种模式之间切换。

### Demo 截图

<p align="center">
  <img src="docs/assets/demo_standard_mode.png" alt="标准DEMO截图" width="860"/>
</p>

---

## 📁 目录结构

```
agent-digital-twin/
├── README.md                      # 本文件
├── LICENSE                        # MIT
├── CONTRIBUTING.md                # 贡献指南
│
├── docs/                          # 文档与资源
│   ├── architecture.svg           # ★ 五元架构图（SVG 内联渲染）
│   ├── assets/
│   │   └── demo_standard_mode.png # Demo 运行截图
│   └── planning/                  # 规划文档与汇报材料
│       ├── P0-P3全期执行总览.html
│       ├── P0评审会议材料.html
│       ├── P0需求规格与标准符合性基线.html
│       ├── P0评审汇报.pptx
│       ├── P1启动包_几何内核与数据底座打通.html
│       ├── P2启动包_仿真保真与智能层集成.html
│       ├── P3启动包_系统集成与测评取证.html
│       ├── 华为OGG_Agent数字孪生论证分析.html
│       ├── 智能数字孪生系统建设规划方案.html
│       └── build_pptx.js / deck_text.txt
│
├── P1_Demo零依赖原型/             # ★ 核心：零依赖 Demo
│   ├── requirements.txt           # Python 依赖
│   ├── demo_unified.py            # 统一入口（标准DEMO + 客户定制 双模式）
│   ├── demo_app.py                # 几何/传感/仿真/数据底座 四面板渲染原语
│   ├── factory_sim_core.py        # 5 类工厂仿真内核
│   ├── planner_core.py            # 客户化规划器核心
│   ├── demo_databus_sqlite.py     # 数据底座（SQLite + DataSource 适配层）
│   ├── demo_geometry_occ.py       # OGG 几何建模桥接
│   ├── demo_factory.py            # 工厂级选择器 + 参数滑块
│   ├── demo_planner.py            # 规划器 UI
│   ├── demo_databus_app.py        # 数据底座探查 UI
│   ├── demo_agent_local_llm.py    # 本地 LLM Agent 演示
│   ├── p2_intelligence.py         # P2 智能层（诊断/预测/决策 三类 Agent）
│   ├── p2_cae_fidelity.py         # P2 装备级 CAE 保真（FEM 梁 + FDM 热传导）
│   ├── p2_fem3d.py                # P2-C 3D 实体有限元（Hex20 二次单元，对标 ANSYS SOLID186）+ 动力学（模态/瞬态）
│   ├── p3_assessment.py           # P3 集成测评（系统测试 + GB/T 符合性 + 成熟度）
│   ├── p4_closed_loop.py          # P4 闭环自治（L4 自主优化硬证据：监测→自主增资→重仿验证）
│   ├── industry_templates.py      # 行业模板库（5 类工厂可复用规划模板）
│   ├── make_demo_preview.py       # 静态预览页生成
│   └── mes_export_sample.csv      # MES 样例数据
│
└── P1_W1_开工脚手架/             # OGG 几何内核编译 / 容器化脚手架
    ├── CMakeLists.txt / Dockerfile / docker-compose.yml
    ├── build_ogg.sh / hello_geometry.cpp
    ├── local-stack/               # 本地消息/时序中间件栈
    └── README.md
    # 注：ogg_src/（1.1G Open CASCADE 上游源码）不入库，请按 README 自行拉取
```

---

## 🔧 核心模块说明

### 数据底座适配层 (`demo_databus_sqlite.py`)
通过 `DataSource` 抽象内置三类数据源，上线真实系统后只需替换实现：
- `SimulatedSource`：默认，本地随机过程模拟设备信号
- `CsvFileSource`：从 MES 导出的 CSV 回放
- `MesRestSource`：对接真实 MES/SCADA 的 REST 接口（占位实现）

`LivePipeline(source=...)` 统一驱动"采集 → 总线分发 → 时序落库 → 持久化"。

### 工厂仿真内核 (`factory_sim_core.py`)
`FACTORY_LIBRARY` 内含 5 类工厂原型，每类含工位拓扑、节拍、设备数、痛点与推荐建设要点。支持新建厂规划与存量厂优化两种场景。

### 客户化规划器 (`planner_core.py`)
`detect_factory_type(text)`（关键词启发式）→ `derive_plan(...)`（按系统节拍 `T = 年工时 / 年产量` 反算各工位设备数）→ `render_plan_html()`（导出规划书）。

示例：输入"新能源汽车动力电池包"→ 自动判定为汽车流水线 → 反算设备 → 仿真验证产能可达性 **99.9%**。

---

## 🛣️ 四期落地路线

| 阶段 | 名称 | 目标 | 状态 |
|------|------|------|------|
| **P0** | 总体论证 | 需求规格、标准符合性、方案评审基线 | ✅ 已完成 |
| **P1** | 内核打通 | 几何内核 + 数据底座打通（零依赖原型） | ✅ 已完成 & 公开 |
| **P2** | 仿真保真 | 仿真精度提升 + MAS 智能层集成 + CAE 保真 | ✅ 已完成 |
| **P3** | 集成测评 | 系统集成测试、取证、合规验证 | ✅ 已完成 |

---

## 🤝 参与贡献

欢迎 Issue / PR / Star！详见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

- 报告问题 → [GitHub Issues](https://github.com/iduyuhe/agent-digital-twin/issues) 或 [Gitee Issues](https://gitee.com/i4hub/agent-digital-twin/issues)
- 提交代码 → Fork → 创建功能分支 → 提交 PR
- 讨论交流 → [GitHub Discussions](https://github.com/iduyuhe/agent-digital-twin/discussions)

---

## 📄 开源协议

本项目以 **[MIT License](./LICENSE)** 开源。自由使用、修改、分发，请保留版权声明。

---

## 🔗 双平台同步

本仓库同时在 GitHub 与 Gitee 开源，内容保持一致：

| 平台 | 地址 |
|------|------|
| **GitHub** | https://github.com/iduyuhe/agent-digital-twin |
| **Gitee** | https://gitee.com/i4hub/agent-digital-twin |

---

<p align="center">
  <sub>© 2026 工业5点0产业生态联盟 · Industrial 5.0 Industry Ecosystem Alliance</sub>
</p>
