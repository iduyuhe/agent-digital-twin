# v1.4.0 — 瞬态动力学 + 模态分析（对标 ANSYS 模态/瞬态求解）

**发布日期：2026-08-13**

---

## 变更概览

本版本是「重资产替换商业求解器」路线的**第二个里程碑**——在 v1.3.0 的 Hex20 三维实体静力基础上，补齐 **动力学核心能力**（模态分析 + 瞬态时程积分），使自研求解器覆盖商业 CAE 的三大招牌场景：

| 能力 | v1.3.0 | **v1.4.0 ✅** | 商业对标 |
|------|--------|---------------|----------|
| 静力结构分析 | ✅ Hex20 | ✅ | ANSYS SOLID186 |
| 模态分析（固有频率） | — | **✅ eigsh 广义特征问题** | ANSYS Modal |
| 瞬态动力学（Newmark-β） | — | **✅ 平均加速度法** | ANSYS Transient |

### 核心新增

| 新增 | 说明 |
|------|------|
| **一致质量矩阵** `hex20_mass_matrix()` | 27 点高斯积分，Kronecker I₃ 扩展至 60×60 DOF |
| **模态求解器** `modal_cantilever()` | scipy.sparse.linalg.eigsh 广义特征问题 Kφ=ω²Mφ，移频法取最低阶 |
| **瞬态积分器** `transient_step_cantilever()` | Newmark-β（β=¼, γ=½）平均加速度法，无条件稳定；自适应时步 |
| **解析频率谱** `cantilever_euler_freqs()` | 双弯曲方向 + 轴向 + 扭转，升序排列，与 FEM 排序模态一一对标 |
| **动力学标定** ×2 | 模态基频误差 ≤0.8% / 阶跃响应 DAF 误差 ≤0.6% |
| **瞬态时程可视化** `transient_timehistory_plotly()` | Plotly 交互式时程图（DAF 标注）+ matplotlib 静态资产 |

### 技术架构

```
┌───────────────────────────────────────────────────────┐
│              p2_fem3d.py 动力学模块                    │
│                                                       │
│  ┌──────────┐   ┌────────────┐   ┌──────────────┐    │
│  │ hex20_   │→  │ _assemble_  │→  │ Kff, Mff     │    │
│  │ stiffness│   │ KM()       │   │ (BC applied) │    │
│  └──────────┘   └────────────┘   └──────┬───────┘    │
│  ┌──────────┐   ┌────────────┐          │            │
│  │ hex20_   │→  │ _assemble_  │          ↓            │
│  │ mass_mat │   │ KM()       │   ┌──────────────┐    │
│  └──────────┘   └────────────┘   │ eigsh(K,M)   │    │
│                                 │ → ω², φ      │    │
│                                 └──────┬───────┘    │
│                                        ↓             │
│  ┌──────────────────────────────────────────────┐     │
│  │ Newmark-β (β=¼, γ=½, C=0, unconditionally stable)│
│  │ Khat = K + M/(βdt²)  → splu(Khat)           │     │
│  │ u_{n+1} = Khat⁻¹·(F_{n+1} + M·predictor)   │     │
│  └──────────────────────────────────────────────┘     │
│                                                       │
│  基准线：Euler-Bernoulli 固有频率 + DAF=2.0         │
└───────────────────────────────────────────────────────┘
```

### 标定结果

```
P2-FEM3D 动力学标定报告（Hex20 二次单元 + 一致质量矩阵）

场景                        解析基线        数值均值       相对误差    达标
─────────────────────────────────────────────────────────────────────
beam_3d_cantilever_hex20   6.128e-01 m     6.081e-01 m    0.513%      ✅ PASS
beam_3d_tension_hex20      1.072e-05 m     1.066e-05 m    0.645%      ✅ PASS
beam_3d_modal_hex20        17.84 Hz        17.97 Hz       0.773%      ✅ PASS
beam_3d_transient_hex20    2.000 (DAF)     1.988 (DAF)     0.593%      ✅ PASS

>>> P2_FEM3D_OK <<<
```

**模态亮点（代表工况 L=1m, b=30mm, h=40mm, 钢）：**

| 阶数 | FEM (Hz) | Euler-Bernoulli (Hz) | 误差 |
|------|----------|---------------------|------|
| 1（y 向弯曲） | 25.24 | 25.13 | 0.45% |
| 2（z 向弯曲） | 33.62 | 33.50 | 0.36% |
| 3（y 向二阶） | 157.65 | 157.46 | 0.12% |
| 4（z 向二阶） | 209.27 | 209.94 | 0.32% |

**瞬态亮点：阶跃载荷动态放大系数 DAF = 1.988（解析 = 2.000，误差 0.58%）**

## 文件变更

```
P1_Demo零依赖原型/
├── p2_fem3d.py                  # 🔧 新增：动力学求解器（~350 行新增）
├── demo_unified.py              # 🔧 CAE 面板合并 9 场景 + 动力学子面板
docs/
├── RELEASE_NOTES_v1.4.0.md      # 🆕 本文件
├── assets/
│   ├── demo_fem3d_deformation.png  # （v1.3.0 资产）
│   └── demo_fem3d_transient.png  # 🆕 瞬态时程图（73KB）
README.md                         # 🔧 特性列表更新
```

## 快速开始

```python
# === 模态分析 ===
from p2_fem3d import modal_cantilever, cantilever_euler_freqs

freqs, Phi, mesh_info, params = modal_cantilever(
    L=1.0, b=0.03, h=0.04, E=210e9, nu=0.3, rho=7850,
    nx=16, ny=4, nz=4, n_modes=4)
ana = cantilever_euler_freqs(1.0, 0.03, 0.04, 210e9, 0.3, 7850, 4)
for i in range(4):
    print(f"Mode {i+1}: {freqs[i]:.2f} Hz (FEM) vs {ana[i]:.2f} Hz (analytic)")

# === 瞬态阶跃响应 ===
from p2_fem3d import transient_step_cantilever

t_arr, tip_hist, peak, static_tip, _ = transient_step_cantilever(
    L=1.0, b=0.03, h=0.04, E=210e9, nu=0.3, rho=7850,
    P=1000.0, nx=16, ny=4, nz=4)
print(f"Dynamic Amplification Factor: {peak/abs(static_tip):.4f} "
      f"(analytic = 2.0000)")
```

## 四期路线总览

```
v1.0.0  →  P0+P1  ✅  零依赖 Demo + 五元架构
v1.1.0  →  P2+P3  ✅  仿真保真 + 智能层 + CAE + 集成测评
v1.2.0  →  模板库  ✅  5 类工厂可复用规划模板
v1.3.0  →  3D FEM  ✅  Hex20 实体有限元（对标 SOLID186）
v1.4.0  →  动力学  ✅  模态分析 + 瞬态 Newmark-β（对标 Modal/Transient）
                    ↓
            后续方向：
            A. 非线性材料 / 接触分析
            B. 本地 LLM 接入 MAS Agent
            C. CESI 正式取证 → L4
            D. 更多行业模板
```

## 双平台链接

| 平台 | Release | 仓库 |
|------|---------|------|
| GitHub | [Releases](https://github.com/iduyuhe/agent-digital-twin/releases/tag/v1.4.0) | [iduyuhe/agent-digital-twin](https://github.com/iduyuhe/agent-digital-twin) |
| Gitee | [Releases](https://gitee.com/i4hub/agent-digital-twin/releases) | [i4hub/agent-digital-twin](https://gitee.com/i4hub/agent-digital-twin) |
