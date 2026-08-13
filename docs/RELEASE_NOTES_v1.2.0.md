# 工业智能数字孪生系统 · v1.2.0

> Industrial Intelligent Digital-Twin System — Industry Template Library for Reusable Customer Planning

v1.2.0 在 v1.1.0（完整四期 P0–P3 落地）的基础上，新增**行业模板库**——把 5 类工厂仿真原型升级为**可复用的客户化规划模板层**，让"输入公司/产品 → 自动出规划书"的链路从"裸判定"进化为"行业最佳实践预填"。同时补齐了 `planner_core` 的 `type_override` 锁定机制，确保选模板后原型判定不再因描述微调而漂移。

---

## 📋 变更概览

### 行业模板库（核心新增）

| 维度 | 内容 |
|------|------|
| **5 类行业模板** | 机加工 / 装备装配 / 半导体 / 汽车流水线 / 电子组装，每类含行业画像、细分领域、典型产品 |
| **典型客户参数预设** | 年产(万)、班制、工作天数、班时、占地、自动化率 —— 一键套用到"客户定制"模式 |
| **参考 KPI 基准** | 工位数量、基线设备数、最长工位工序时长、设计产能（由 `factory_sim_core` 动态计算，避免硬编码漂移） |
| **孪生目标等级** | 每行业标注 L1~L3 数字孪生成熟度目标（半导体→L3 预测孪生，其余→L2 制造孪生） |
| **规划假设 & 标杆** | 每行业沉淀可溯源、可校正的规划假设与行业基准参考，让规划书可被客户评审质询 |

**对外 API（`industry_templates.py`）**：
- `list_industry_templates()` —— 返回 `[(key, display, tags)]` 供 UI 下拉
- `get_template(key)` —— 合并工厂原型基线 + 规划层增强 + **动态参考 KPI**
- `apply_template(key, overrides)` —— 返回可直接喂给 `planner_core.derive_plan` 的入参（含 `type_override` 锁定原型）
- `export_templates_json(path)` —— 导出全部模板为 JSON，供销售/方案团队离线编辑行业包（自测导出 9426 字符）

### 规划器增强

| 构件 | 变更 |
|------|------|
| `planner_core.derive_plan` | 新增 `type_override` 参数；传入行业模板时锁定工厂原型，杜绝描述微调导致的误判 |
| `demo_unified.render_custom` | "客户定制"模式新增**行业模板选择器**：选模板 → 预填产品描述 + 典型参数 → `derive_plan(type_override)` 一键生成；导出规划书时若表单留默认则自动套用模板参数 |

### 文件变更

```
新增文件：
  industry_templates.py          # 行业模板库（5 类工厂可复用规划模板 + JSON 导出）

修改文件：
  planner_core.py                # derive_plan 新增 type_override 锁定原型
  demo_unified.py                # 客户定制模式新增行业模板选择器 + 自动套用
  README.md                       # 核心特性补充"行业模板库"条目，目录树补 industry_templates.py
```

> 注：本版本无仿真/智能/CAE 算法改动，P2/P3 全部标尺（±0.5% / ≤±0.004% / 100% / 8·9 / L3）维持不变。

---

## 🏭 行业模板清单

| 模板 key | 行业 | 孪生目标 | 典型产品（节选） | 典型年产量 |
|----------|------|---------|----------------|-----------|
| `machining` | 精密机械加工 | L2 制造孪生 | 精密齿轮箱壳体 / 航空铝合金支架 | 30 万 |
| `assembly` | 装备总装 | L2 制造孪生 | 大型工程机械整机 / 工业减速机 | 5 万 |
| `semiconductor` | 晶圆制造 | **L3 预测孪生** | 12 寸逻辑晶圆 / 功率半导体模组 | 20 万 |
| `automotive` | 汽车流水线 | L2 制造孪生 | 乘用车整车 / 动力电池包 | 30 万 |
| `electronics` | 电子组装 | L2 制造孪生 | 智能手机整机 / 锂电池模组 | 100 万 |

每个模板均含：`industry_tags` / `sub_sectors` / `typical_products` / `typical_params` / `planning_assumptions` / `benchmark` / `twin_target_level`，外加由内核动态计算的 `reference_kpi`。

---

## 🏗️ 架构

五元架构 × 双引擎（华为 OGG 几何引擎 + 通用 MAS Agent）不变。v1.2.0 在**应用层**新增"行业模板层"作为规划器上游：

```
┌─────────────────────────────────────────────────────────┐
│                    应用层                                  │
│  demo_unified.py (4 modes: DEMO / 定制 / P2 / P3)         │
│  └─ 客户定制模式 ──► [行业模板选择器] ──► derive_plan      │
├───────────────────────┬─────────────────────────────────┤
│     行业模板层 (新增)   │   智能层 / 仿真保真 / CAE / 测评   │
│  industry_templates    │   p2_* / factory_sim_core /      │
│  (5 类模板 + JSON 导出) │   p2_cae_fidelity / p3_assessment│
├───────────────────────┴─────────────────────────────────┤
│              数据底座 / 几何内核 (P1)                       │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

```bash
# 1. 克隆（二选一）
git clone https://github.com/iduyuhe/agent-digital-twin.git
git clone https://gitee.com/i4hub/agent-digital-twin.git

# 2. 安装依赖
cd agent-digital-twin/P1_Demo零依赖原型
pip install -r requirements.txt   # streamlit / plotly / numpy / pandas / simpy / scipy

# 3. 启动统一 Demo
python -m streamlit run demo_unified.py --server.port 8505
# 浏览器打开 http://localhost:8505
# 切换到「客户定制」→ 在侧栏选择行业模板 → 一键预填并生成规划书
```

### 程序化复用行业模板

```python
import industry_templates as it

# 列出全部模板
for k, disp, tags in it.list_industry_templates():
    print(k, disp, tags)

# 套用半导体模板 → 直接喂给规划器
ap = it.apply_template("semiconductor")
# ap = {"product": "...", "params": {...}, "type_override": "semiconductor"}

# 离线导出全部模板为 JSON（供销售/方案团队编辑行业包）
it.export_templates_json("industry_pack.json")
```

---

## Demo 截图

<p align="center">
  <img src="docs/assets/demo_industry_templates.png" alt="行业模板库客户定制模式截图" width="860"/>
</p>

> 截图展示了"客户定制"模式下的**行业模板选择器**：选定行业后，产品描述与典型参数自动预填，规划器锁定原型并即时生成建设方案与 HTML 规划书。

---

## 四期建设路线（全部完成 ✅）

- **P0** ✅ 需求规格 / 标准符合性基线 / 评审
- **P1** ✅ 几何内核与数据底座打通（零依赖 Demo + OGG 脚手架）
- **P2** ✅ 仿真保真与智能层集成（蒙特卡洛标定 ±0.5% + 三类 Agent + FEM/FDM CAE）
- **P3** ✅ 系统集成与测评取证（9 项测试 100% + GB/T 8/9 + CESI L3）

> v1.2.0 为 P0–P3 稳定态之上的**应用层增强**：把验证过的工厂原型沉淀为可复用行业模板，缩短从"线索"到"可评审规划书"的距离。

---

## 双平台

- GitHub：https://github.com/iduyuhe/agent-digital-twin/releases/tag/v1.2.0
- Gitee：https://gitee.com/i4hub/agent-digital-twin/releases

## 许可证

[MIT](LICENSE)

---

*从 v1.0.0 到 v1.2.0：零依赖原型 → 仿真保真 → 智能层 → 集成测评 → 行业模板库，四期路线 + 应用增强双线贯通。*
