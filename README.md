# 工业智能数字孪生系统 · 零依赖参考实现

**Industrial Intelligent Digital-Twin — Zero-Dependency Reference Implementation**

> 华为 OGG 几何内核 + 通用 MAS Agent 双引擎 · 五元架构 · 四期落地路线（P0–P3）
> 由 **工业5点0产业生态联盟** 开源维护

---

## 1. 项目简介

本项目是一套**可本地零依赖运行**的工业智能数字孪生参考实现，目标是把"数字孪生"从 PPT 概念落到可演示、可二次开发的工程骨架：

- **几何内核**：基于华为 OGG（Open Geometry Kernel，OpenCASCADE 封装）的轻量几何建模能力，给出厂房 / 设备 / 产线的 3D 数字实体原型。
- **数据底座**：用 SQLite + 内存队列**替代** EMQX + IoTDB，零外部依赖即可演示"设备 → 消息总线 → 时序库 → 持久化"的完整数据链路，并预留 `DataSource` 适配层（模拟 / CSV / MES-REST 三类），待真实 MES/SCADA 上线后可无缝切换。
- **离散事件仿真**：基于 SimPy 的产线产能 / 瓶颈 / 可达性仿真，支持新建厂规划与存量厂优化两种场景、5 类工厂原型（机加工 / 装备装配 / 半导体 / 汽车流水线 / 电子组装）。
- **MAS 智能规划**：以"公司 / 产品 → 工厂类型判定 → 按系统节拍反算设备数 → 仿真验证"的闭环，自动生成客户化工厂数字孪生建设方案与可下载规划书。

整套 Demo **仅需 Python（streamlit / plotly / numpy / pandas / simpy）**，无需 Docker、无需联网、无需任何商业中间件即可跑通。

---

## 2. 双引擎架构

| 引擎 | 职责 | 在本仓库的体现 |
|------|------|----------------|
| **华为 OGG 几何内核** | 厂房 / 设备 / 产线的三维几何建模 | `P1_W1_开工脚手架/`（OGG 编译与 Docker 化）+ `demo_geometry_occ.py` |
| **通用 MAS Agent** | 多智能体协同的规划 / 诊断 / 预测 | `planner_core.py` + `demo_agent_local_llm.py` |

两者通过统一的数据底座与仿真内核解耦协作：**几何层**产出数字实体，**数据层**汇聚实时/历史信号，**仿真层**验证产能，**智能层**基于前三者做规划与决策。

---

## 3. 五元架构与四期路线（P0–P3）

- **五元架构**：几何内核 · 数据底座 · 离散仿真 · 智能规划 · 集成测评。
- **四期路线**：
  - **P0** 总体论证与评审基线（需求规格、标准符合性、方案论证）
  - **P1** 几何内核打通 + 数据底座打通（零依赖原型）
  - **P2** 仿真保真 + 智能层集成
  - **P3** 系统集成与测评取证

各阶段启动包 / 论证材料以 HTML 形式置于仓库根目录（见下方目录结构）。

---

## 4. 目录结构

```
agent-digital-twin/
├── README.md                      # 本文件
├── LICENSE                        # MIT
├── P0-P3全期执行总览.html         # 五元架构 / 四期路线 / 三标尺总览
├── P0评审会议材料.html
├── P0需求规格与标准符合性基线.html
├── P0评审汇报.pptx
├── P1启动包_几何内核与数据底座打通.html
├── P2启动包_仿真保真与智能层集成.html
├── P3启动包_系统集成与测评取证.html
├── 华为OGG_Agent数字孪生论证分析.html
├── 智能数字孪生系统建设规划方案.html
├── build_pptx.js / deck_text.txt # PPTX 构建源
│
├── P1_Demo零依赖原型/             # ★ 核心：零依赖 Demo
│   ├── demo_unified.py            #   统一入口（标准DEMO + 客户定制 双模式）
│   ├── demo_app.py                #   几何/传感/仿真/数据底座 四面板渲染原语
│   ├── factory_sim_core.py        #   5 类工厂仿真内核
│   ├── planner_core.py            #   客户化规划器核心（类型判定/节拍反算/规划书）
│   ├── demo_databus_sqlite.py    #   数据底座（SQLite + 队列 + DataSource 适配层）
│   ├── demo_geometry_occ.py       #   OGG 几何建模桥接
│   ├── demo_factory.py            #   工厂级选择器 + 参数滑块
│   ├── demo_planner.py            #   规划器 UI
│   ├── demo_databus_app.py        #   数据底座探查 UI
│   ├── demo_agent_local_llm.py    #   本地 LLM Agent 演示
│   ├── make_demo_preview.py       #   静态预览页生成
│   └── mes_export_sample.csv      #   MES 样例数据（CSV 适配层输入）
│
└── P1_W1_开工脚手架/             # OGG 几何内核编译 / 容器化脚手架
    ├── CMakeLists.txt / Dockerfile / docker-compose.yml
    ├── build_ogg.sh / hello_geometry.cpp
    ├── local-stack/               # 本地消息/时序中间件栈（compose）
    └── README.md
    # 注：ogg_src/（1.1G Open CASCADE 上游源码）不入库，请按 README 自行拉取
```

---

## 5. 快速开始

```bash
# 1. 安装依赖（仅需 Python 3.10+）
pip install streamlit plotly numpy pandas simpy

# 2. 启动统一 Demo（标准DEMO + 客户定制 双模式）
streamlit run P1_Demo零依赖原型/demo_unified.py --server.port 8505
# 浏览器打开 http://localhost:8505
```

统一 Demo 顶部可在 **「标准DEMO」**（以机加工标杆产线讲清系统能力）与 **「客户定制」**（输入公司/产品+参数，自动生成你的工厂方案）之间切换。

其它可选服务：

```bash
streamlit run P1_Demo零依赖原型/demo_databus_app.py --server.port 8502   # 数据底座深探
streamlit run P1_Demo零依赖原型/demo_factory.py     --server.port 8503   # 工厂级参数调优
streamlit run P1_Demo零依赖原型/demo_planner.py     --server.port 8504   # 客户化规划器
```

---

## 6. 核心模块说明

### 6.1 数据底座适配层（`demo_databus_sqlite.py`）
通过 `DataSource` 抽象，内置三类数据源，上线真实系统后只需替换实现：

- `SimulatedSource`：默认，本地随机过程模拟设备信号
- `CsvFileSource`：从 MES 导出的 CSV 回放
- `MesRestSource`：对接真实 MES/SCADA 的 REST 接口（占位实现）

`LivePipeline(source=...)` 统一驱动"采集 → 总线分发 → 时序落库 → 持久化"。

### 6.2 工厂仿真内核（`factory_sim_core.py`）
`FACTORY_LIBRARY` 内含 5 类工厂原型，每类含工位拓扑、节拍、设备数、痛点与推荐建设要点。`simulate_new_plant()` / `simulate_existing_plant_optimization()` 分别输出产能、瓶颈利用率与产能可达性。

### 6.3 客户化规划器（`planner_core.py`）
`detect_factory_type(text)`（关键词启发式）→ `derive_plan(...)`（按系统节拍 `T = 年工时 / 年产量` 反算各工位设备数）→ `render_plan_html()`（导出规划书）。示例：输入"新能源汽车动力电池包"可自动判定为汽车流水线，反算设备并仿真验证产能可达性 99.9%。

---

## 7. 开源协议

本项目以 **MIT License** 开源（见 `LICENSE`）。欢迎 Issue / PR / Star。

---

## 8. 双平台同步

本仓库同时在 GitHub 与 Gitee 开源，内容保持一致：

- GitHub：https://github.com/iduyuhe/agent-digital-twin
- Gitee：https://gitee.com/i4hub/agent-digital-twin

---

© 2026 工业5点0产业生态联盟 · Industrial 5.0 Industry Ecosystem Alliance
