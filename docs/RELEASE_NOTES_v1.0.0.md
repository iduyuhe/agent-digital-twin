# 工业智能数字孪生系统 · v1.0.0

> Industrial Intelligent Digital-Twin System — First Open-Source Release

首个公开版本。本项目提供一套**零依赖、可本地运行**的工业数字孪生参考实现，覆盖从几何建模、数据底座、离散事件仿真到 MAS 智能规划的完整链路，可作为企业数字孪生平台的建设蓝本。

---

## 核心能力

| 能力域 | 说明 |
|--------|------|
| 🧊 **几何内核** | 基于华为 OGG（Open Geometry Kernel，LGPL 2.1）的 CAD/BREP 几何能力；提供零依赖的网格生成与 3D 可视化参考实现 |
| 🚌 **数据底座** | 轻量数据总线（≈EMQX 发布/订阅）+ 时序库（≈IoTDB，SQLite 存储），预留 `DataSource` 适配层，未来可无缝接入真实 MES / SCADA |
| 🏭 **离散仿真** | SimPy 离散事件仿真，支持 5 类工厂原型（机加工 / 装备装配 / 半导体 / 汽车流水线 / 电子组装），按节拍反算设备数、测算产能可达性 |
| 🤖 **MAS 智能规划** | 通用多智能体规划器：输入公司 / 产品 / 参数，自动判定工厂原型、推导设备配置并仿真验证，输出可下载的数字孪生建设方案 |
| 🖥️ **统一双模式 Demo** | 「标准 DEMO / 客户定制」单应用切换；标准模式以标杆产线讲清能力，定制模式复用同一引擎落到客户工厂 |

## 架构

五元架构（物理实体 / 数字实体 / 数据底座 / 智能层 / 应用层）× 双引擎（华为 OGG 几何引擎 + 通用 MAS Agent）。详见 `docs/architecture.svg`。

## 快速开始

```bash
# 1. 克隆（二选一）
git clone https://github.com/iduyuhe/agent-digital-twin.git
git clone https://gitee.com/i4hub/agent-digital-twin.git

# 2. 安装依赖
cd agent-digital-twin/P1_Demo零依赖原型
pip install -r requirements.txt   # streamlit / plotly / numpy / pandas / simpy

# 3. 启动统一 Demo（标准 DEMO + 客户定制 双模式）
python -m streamlit run demo_unified.py --server.port 8505
# 浏览器打开 http://localhost:8505
```

## 目录结构

```
agent-digital-twin/
├── P1_Demo零依赖原型/      # 零依赖 Demo 核心源码（几何/数据底座/仿真/规划/MAS）
├── P1_W1_开工脚手架/       # 华为 OGG 几何内核编译与容器化（ogg_src 1.1G 上游源码不入库）
├── docs/                   # 架构图 / Demo 截图 / 规划文档
├── README.md               # 项目门面（中英双语）
├── CONTRIBUTING.md         # 贡献指南
└── LICENSE                 # MIT
```

## 四期建设路线（P0–P3）

- **P0** ✅ 需求规格 / 标准符合性基线 / 评审 —— 已完成
- **P1** 🔵 几何内核与数据底座打通 —— 当前版本主体（零依赖 Demo + OGG 脚手架）
- **P2** ⏳ 仿真保真与智能层集成 —— 规划中
- **P3** ⏳ 系统集成与测评取证 —— 规划中

## 双平台

- GitHub：https://github.com/iduyuhe/agent-digital-twin
- Gitee：https://gitee.com/i4hub/agent-digital-twin

## 许可证

[MIT](LICENSE) —— 可自由用于商业与开源衍生，请保留版权声明。

---

*本版本为首个开源里程碑。欢迎通过 Issue / PR 参与共建。*
