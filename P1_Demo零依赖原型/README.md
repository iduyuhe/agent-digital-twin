# 智能数字孪生系统 · 零依赖 Demo 原型

## 目的
在**最低硬件门槛**上先做出可运行的 Demo，证明"几何建模 → 实时同步 → 智能诊断"端到端闭环可行，
把"编译 OGG/OCCT（重型 C++）"这个前置从 Demo 关键路径上拿掉。正式交付时再把占位组件换回正式构件。

## 降依赖映射表
| 正式构件（P1 规划） | Demo 轻量占位 | 移除的依赖 |
|---|---|---|
| OGG / OCCT 源码编译（C++，8核16G Linux）| numpy + plotly 生成几何体 | 免编译、免 Linux 构建机、免云 |
| EMQX + IoTDB 数据底座（MQTT broker + JVM）| Python 队列 + SQLite 时序 | 免 broker、免 JVM |
| 通用 MAS 接口 + 本地 LLM（GPU）| 规则引擎（阈值/预测）| 免 GPU、免大模型 |

## 运行环境
- 任意 Windows / Linux / macOS 笔记本或台式机
- Python 3.9+（推荐 3.10/3.11）
- **无需云服务器、无需 Docker、无需编译 C++、无需 GPU**
- 最低实测：4 核 8G 即可流畅运行

## 启动步骤
```bash
# 1. 进入目录
cd P1_Demo零依赖原型

# 2. 创建并激活虚拟环境（可选但推荐）
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. 安装依赖（纯 Python 包，pip 直接装，无编译）
pip install -r requirements.txt

# 4. 启动 Demo
streamlit run demo_app.py
```
浏览器自动打开 http://localhost:8501 ，即可看到：
- 左侧：数字实体 3D 几何模型（plotly 渲染）
- 右侧：温度/振动/转速实时曲线（每秒刷新）
- 底部：规则引擎触发的故障诊断/状态预测告警

### ★ 统一 Demo（推荐单一入口，端口 8505）
把「标准DEMO」与「客户化规划器」合成一个应用，顶部切换，符合"先看标准能力→再定制到客户工厂"的正常叙事：
```bash
streamlit run demo_unified.py --server.port 8505
```
- 标准DEMO：以**单一标杆参考工厂（机加工精密产线）**为主角，展示 几何3D / 实时传感 / 工厂仿真 / 数据底座 四面板；可下拉探索其它工厂类型。
- 客户定制：填入 公司/产品 + 客户参数（年产量·班制·节拍·占地·自动化率），自动判定工厂原型、按节拍反算设备、仿真验证产能，并**复用标准引擎渲染"您的工厂实景"**，可下载规划书 HTML。

## 本目录文件清单
| 文件 | 用途 | 对应替换清单周次 |
|---|---|---|
| `demo_unified.py` | **统一 Demo（推荐入口 8505）**：标准DEMO + 客户化规划器 双模式，复用同一套几何/传感/仿真/数据底座引擎 | 整合 |
| `demo_app.py` | 主 Demo：Streamlit 单页（3D 几何 + 实时曲线 + 规则告警）| 第 0 周起点 |
| `demo_geometry_occ.py` | 几何层正式路径：pythonocc-core 真 OCCT 建模 + STEP 导出（含 numpy fallback）| W1 |
| `demo_agent_local_llm.py` | 智能层正式路径：Ollama 本地 LLM + 通用 MAS 接口（含规则 fallback）| W4 |
| `factory_sim_core.py` | 工厂级仿真核心：SimPy 离散事件仿真，**工厂类型库**（机加工/装备装配/半导体/汽车流水线/电子组装，各自工艺拓扑·设备·设计产能·数字孪生建模重点），双场景（新建厂验证 + 存量产能优化），按 `factory_type` 驱动 | W2（工厂级）|
| `demo_factory.py` | 工厂级仿真可视化：Streamlit 单页（**工厂类型下拉** + **侧栏每工位节拍/机器数滑块实时重算** + 双场景 KPI + 利用率柱状图 + 本厂建设方案要点）| W2（工厂级）|
| `demo_databus_sqlite.py` | **数据底座核心**：DataBusLite(≈EMQX 消息路由) + TsStore(≈IoTDB 时序库,SQLite) + **DataSource 适配层**（SimulatedSource/CsvFileSource/MesRestSource），纯标准库零依赖；落库+回查验证 | W1（数据层）|
| `demo_databus_app.py` | 数据底座可视化：Streamlit 单页（实时遥测回查 + SQLite 落库查询面板）| W1（数据层）|
| `mes_export_sample.csv` | MES/SCADA 导出样例 CSV（由 `gen-sample` 生成，用于离线验证数据源接缝）| W1（数据层）|
| `从Demo到正式_替换清单.html` | W1–W6 递进替换排期与门禁（详见）| 全局 |
| `requirements.txt` | 纯 Python 依赖（streamlit/plotly/numpy/pandas/simpy）| — |

### 进阶运行（替换路径验证）
```bash
# 几何层：真 OCCT（需先 pip install pythonocc-core，Python 3.9~3.11）
python demo_geometry_occ.py

# 智能层：本地 LLM（需先 pip install ollama，并 ollama serve && ollama pull deepseek-r1:7b）
python demo_agent_local_llm.py

# 工厂级仿真：SimPy 零依赖（需先 pip install simpy）
python factory_sim_core.py          # 命令行遍历 4 类工厂跑双场景
streamlit run demo_factory.py       # 可视化：下拉切换工厂类型 + 双场景 + 建设方案
streamlit run demo_app.py           # 主 Demo：③ 工厂面板内下拉切换工厂类型（默认机加工）
# 支持工厂类型：machining(机加工) / assembly(装备装配) / semiconductor(半导体) / automotive(汽车流水线) / electronics(电子组装)
# demo_factory.py 侧栏可拖滑块实时调每工位节拍(分)与机器数(1~8)，仿真随之下方重算；"恢复默认参数"按钮复位

# 数据底座：SQLite + 进程内队列（纯标准库，无需 pip）
python demo_databus_sqlite.py       # 命令行：批量落库 + 回查验证
streamlit run demo_databus_app.py   # 实时可视化：路由→落库→回查闭环

# 数据源适配层（解耦"数据从哪来"与总线/落库；当前 MES/SCADA 未安装，默认走模拟器）
python demo_databus_sqlite.py gen-sample mes_export_sample.csv   # 生成 MES/SCADA 导出样例
python demo_databus_sqlite.py replay mes_export_sample.csv       # 用真实 CSV 回放，证明换数据源不换骨架
# 接真 MES/SCADA（待系统安装 + endpoint 就位后启用，替换 LivePipeline 的 source 即可）：
#   from demo_databus_sqlite import LivePipeline, MesRestSource
#   pipe = LivePipeline(source=MesRestSource(endpoint='https://mes.local/api', token='...'))
```
未安装对应依赖时，脚本自动降级或提示；数据底座核心为纯标准库，开箱即跑。

## 与正式方案的衔接
Demo 跑通后，按 P1 启动包路线逐步替换：
1. 几何层：用 `pythonocc-core`（OCCT 的预编译 Python wheel，仍免编译）或正式编译 OGG，替换 numpy 几何体
2. 数据层：用 EMQX + IoTDB（或 OPC UA 直采）替换 SQLite 队列；**数据源接缝已预置**（DataSource 适配层），届时只需把 `LivePipeline`/`simulate_batch` 的 `source` 由 `SimulatedSource` 换成 `CsvFileSource`（历史导出批量回放）或 `MesRestSource`（实时拉取），下游总线/落库/回查零改动
3. 智能层：用通用 MAS 接口接入本地 LLM（Ollama + DeepSeek/GLM 量化版），替换规则引擎

架构契约保持一致，替换是"换引擎不换骨架"。

## 注意
- Demo 中的几何/同步/仿真数值为**概念验证占位**，不构成 GB/T 45626 合规性证据
- 正式合规需按规划方案走 CESI 成熟度/可信性测评
