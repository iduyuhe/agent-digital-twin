# v1.3.0 — 3D 实体有限元求解器（Hex20，对标 ANSYS SOLID186）

**发布日期：2026-08-13**

---

## 变更概览

本版本是 **"重资产替换商业求解器"** 路线的第一个里程碑——从 P2 的 1D 梁单元（Hermite）正式升维到 **3D 实体有限元**，提供对标 ANSYS SOLID186 级别的三维结构静力分析能力。

### 核心新增

| 新增 | 说明 |
|------|------|
| **`p2_fem3d.py`** | Hex20（20 节点二次六面体）3D 实体有限元求解器 |
| **悬臂梁弯曲基准** | 自由端挠度对标 Euler-Bernoulli 解析解，误差 ≤0.51% |
| **单轴拉伸基准** | 轴向位移对标 Saint-Venant 解析解，误差 ≤1.0% |
| **`deformed_mesh_plotly()`** | Plotly 交互式 3D 变形网格可视化 |
| **Demo CAE 面板增强** | 合并展示 7 场景标定结果（5 原有 + 2 新增 3D） |

### 技术亮点

```
┌─────────────────────────────────────────────────────┐
│              p2_fem3d.py 架构                        │
│                                                     │
│  ┌──────────┐   ┌────────────┐   ┌──────────────┐  │
│  │ brick_   │→  │ hex20_     │→  │ _assemble()  │  │
│  │ mesh20() │   │ stiffness()│   │ COO 散射装配  │  │
│  │ 结构化网格│   │ 27 点高斯积分│   │ scipy.sparse │  │
│  └──────────┘   └────────────┘   └──────────────┘  │
│                                                     │
│  ┌─────────────┐  ┌────────────┐  ┌─────────────┐  │
│  │ solve_      │  │ solve_     │  │ calibrate_  │  │
│  │ cantilever()│  │ tension()  │  │ 3d_*()      │  │
│  │ 悬臂梁弯曲  │  │ 单轴拉伸    │  │ 蒙特卡洛标定 │  │
│  └─────────────┘  └────────────┘  └─────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │ deformed_mesh_plotly() — Plotly 3D 变形可视化  │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

#### 为什么选 Hex20（而非 Hex8）

| 维度 | Hex8（线性六面体） | **Hex20（二次六面体）✅** |
|------|-------------------|------------------------|
| 弯曲精度 | 剪切锁定严重（误差 >80%） | **精确表达弯曲场，无锁定** |
| 积分方案 | SRI / QM6 兼容模式（复杂） | **标准 3×3×3 高斯全积分（简洁可靠）** |
| 对标 ANSYS | SOLID185（需特殊处理） | **SOLID186（工业首选实体单元）** |
| 收敛性 | 网格依赖性强 | **二次收敛，粗网格即准** |

#### 标定结果

```
P2-FEM3D 标定报告（Hex20，对标 ANSYS SOLID186）

场景                        解析基线      数值均值       相对误差    达标
─────────────────────────────────────────────────────────────────────
beam_3d_cantilever_hex20   9.443e-02 m  9.475e-02 m   +0.34%      ✅ PASS
beam_3d_tension_hex20       2.000e-04 m  2.013e-04 m   +0.65%      ✅ PASS

>>> P2_FEM3D_OK <<<
```

## 文件变更

```
P1_Demo零依赖原型/
├── p2_fem3d.py                  # 🆕 3D 实体有限元求解器（~580 行）
├── demo_unified.py              # 🔧 CAE 面板合并 7 场景 + 3D 图
docs/
├── RELEASE_NOTES_v1.3.0.md      # 🆕 本文件
├── assets/
│   └── demo_fem3d_deformation.png # 🆕 3D 悬臂梁变形截图
README.md                         # 🔧 特性列表 + 文件树更新
```

## 快速开始

```python
# === 单次运行：悬臂梁 3D 弯曲 ===
from p2_fem3d import solve_cantilever, deformed_mesh_plotly

u, tip_disp, _ = solve_cantilever(
    L=1.0, b=0.03, h=0.05,          # 几何：长×宽×高 (m)
    E=210e9, nu=0.3,                 # 材料：钢
    P=10000,                          # 载荷：端部集中力 (N)
    nx=10, ny=3, nz=3                 # 网格：10×3×3
)
print(f"端部挠度: {tip_disp*1000:.2f} mm")

# 3D 可视化
fig = deformed_mesh_plotly(u, L=1.0, b=0.03, h=0.05,
                           nx=10, ny=3, nz=3, scale=50.0)
fig.show()

# === 完整标定（含蒙特卡洛）===
from p2_fem3d import run_fem3d_calibration
results = run_fem3d_calibration(n_cases=30)
for key, res in results.items():
    print(f"{key}: {res.relative_error_pct:.3f}% {'PASS' if res.meets_caliber else 'FAIL'}")
```

## 四期路线总览

```
v1.0.0  →  P0+P1  ✅  零依赖 Demo + 五元架构
v1.1.0  →  P2+P3  ✅  仿真保真 + 智能层 + CAE + 集成测评
v1.2.0  →  模板库  ✅  5 类工厂可复用规划模板
v1.3.0  →  3D FEM  ✅  Hex20 实体有限元（对标 ANSYS SOLID186）
                    ↓
            后续方向：
            A. 瞬态动力学 / 非线性材料
            B. 本地 LLM 接入 MAS Agent
            C. CESI 正式取证 → L4
            D. 更多行业模板
```

## 双平台链接

| 平台 | Release | 仓库 |
|------|---------|------|
| GitHub | [Releases](https://github.com/iduyuhe/agent-digital-twin/releases/tag/v1.3.0) | [iduyuhe/agent-digital-twin](https://github.com/iduyuhe/agent-digital-twin) |
| Gitee | [Releases](https://gitee.com/i4hub/agent-digital-twin/releases) | [i4hub/agent-digital-twin](https://gitee.com/i4hub/agent-digital-twin) |
