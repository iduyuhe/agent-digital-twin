# Contributing to 工业智能数字孪生系统

**Contributing Guide / 贡献指南**

感谢你对本项目的关注！无论是提 Issue、改进代码、还是补充文档，我们都欢迎。

---

## How to Contribute / 如何贡献

### 1. 报告问题 (Report Issues)

- **GitHub Issues**: https://github.com/iduyuhe/agent-digital-twin/issues
- **Gitee Issues**: https://gitee.com/i4hub/agent-digital-twin/issues
- 提 Issue 时请尽量包含：
  - 复现步骤（Reproduction steps）
  - 环境信息（Python 版本、操作系统）
  - 期望行为 vs 实际行为
  - 截图 / 日志（如有）

### 2. 提交代码 (Pull Requests)

```bash
# 1. Fork 本仓库，然后 clone
git clone https://github.com/<your-username>/agent-digital-twin.git
cd agent-digital-twin

# 2. 创建功能分支
git checkout -b feature/your-feature-name

# 3. 安装依赖
pip install -r P1_Demo零依赖原型/requirements.txt

# 4. 开发 & 测试
#    运行 Demo 确认无回归：
streamlit run P1_Demo零依赖原型/demo_unified.py --server.port 8505

# 5. 提交（请用清晰的 commit message）
git add .
git commit -m "feat: 添加 xxx 功能"

# 6. 推送 & 创建 PR
git push origin feature/your-feature-name
```

### 3. Commit Message 规范

| 前缀 | 含义 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 支持第6种工厂类型` |
| `fix` | Bug 修复 | `fix: 修正电子组装瓶颈计算` |
| `docs` | 文档变更 | `docs: 更新架构图` |
| `refactor` | 重构 | `refactor: 抽取数据底座适配层接口` |
| `test` | 测试相关 | `test: 补充规划器边界条件测试` |
| `chore` | 构建/工具 | `chore: 更新 requirements.txt` |

### 4. Code Style

- Python 遵循 [PEP 8](https://pep8.org/)
- 中文注释优先，关键接口附英文注释
- 函数/类添加 docstring
- 保持与现有代码风格一致

## Project Structure / 项目结构概览

```
P1_Demo零依赖原型/          # ★ 核心代码目录
├── demo_unified.py           # 统一入口（标准DEMO + 客户定制）
├── demo_app.py               # 四面板渲染原语（几何/传感/仿真/数据底座）
├── factory_sim_core.py       # 5 类工厂仿真内核
├── planner_core.py           # 客户化规划器核心
├── demo_databus_sqlite.py    # 数据底座（SQLite + DataSource 适配层）
├── demo_geometry_occ.py      # OGG 几何建模桥接
└── requirements.txt          # Python 依赖

P1_W1_开工脚手架/            # 华为 OGG 编译与容器化
docs/                         # 文档与资源
├── architecture.svg          # 五元架构图
└── assets/                   # 截图等静态资源
```

## Development Setup / 开发环境搭建

### Prerequisites

- **Python 3.10+**（推荐 3.13）
- 无需 Docker、无需数据库、无需联网

### Quick Start

```bash
# 安装依赖
pip install -r P1_Demo零依赖原型/requirements.txt

# 启动统一 Demo
streamlit run P1_Demo零依赖原型/demo_unified.py --server.port 8505
```

浏览器打开 `http://localhost:8505` 即可看到完整 Demo。

## Areas We Welcome Contributions / 欢迎贡献的方向

- [ ] **新工厂类型**：在 `factory_sim_core.py` 的 `FACTORY_LIBRARY` 中添加新的工厂原型
- [ ] **DataSource 实现**：实现 `MesRestSource` 的真实 MES/SCADA 对接
- [ ] **OGG 几何增强**：更精细的 3D 设备模型、CAD 文件导入
- [ ] **智能层扩展**：更多 Agent 能力（预测性维护、排产优化）
- [ ] **文档完善**：中英双语文档、API 参考、教程
- [ ] **Demo UI 优化**：更好的交互体验、移动端适配
- [ ] **测试覆盖**：单元测试、集成测试、端到端测试

## License / 开源协议

本项目以 [MIT License](../LICENSE) 开源。提交 PR 即表示你同意按 MIT 协议授权你的贡献。

---

有问题？直接开 Issue 或在 Discussions 中讨论。欢迎参与！

© 2026 工业5点0产业生态联盟 · Industrial 5.0 Industry Ecosystem Alliance
