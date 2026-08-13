# -*- coding: utf-8 -*-
"""
P2 仿真保真层 · 3D 实体有限元求解器（构件 C-3D）
==============================================
在 p2_cae_fidelity.py（1D 梁 Hermite 单元 + 2D 热传导 FDM）基础上，
下沉到 **三维实体有限元**，对标商业 CAE 的实体单元（ANSYS SOLID186 类
二十节点二次六面体）：

  • 单元：Hex20 二十节点二次六面体（8 角点 + 12 边中点），Serendipity 族。
  • 积分：3×3×3 高斯（27 点），精确积分至四次项。
  • 优势：二次形函数天然表示梁弯曲的二次轴向位移场 → **无剪切锁定**，
        单层截面即可精确恢复欧拉-伯努利挠度（线性 Hex8 做不到）。
  • 装配：均匀结构化网格 → 参考单元刚度一次计算，按自由度散射装配（COO）。
  • 求解：scipy.sparse 直接法（spsolve）。
  • 标定：蒙特卡洛多工况 → 解析基线（悬臂梁挠度 PL³/3EI / 轴向伸长 PL/EA）对比。

设计原则（延续「降依赖、零商业 license」）：
  纯 numpy + scipy，无 ANSYS / Abaqus / pythonocc 依赖即可跑通 3D 结构静力。
  这是对「重资产替换商业求解器」路线的第一里程碑：用自研轻量二次单元
  覆盖商业 CAE 的招牌能力——三维实体结构静力分析。

运行：python p2_fem3d.py          # 跑自检 + 标定报告
依赖：numpy, scipy（均在 venv 中）。
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

# 复用 P2 标定结果数据结构与材料库（单向导入，避免循环依赖）
from p2_cae_fidelity import CalibrationResult, MATERIALS  # noqa: E402


# ============================================================
#  ① 二十节点六面体（Hex20）形函数
# ============================================================
# 局部节点序（标准 Serendipity 排序）：
#  0-7  角点  (±1,±1,±1)
#  8-11 边中点（沿 ξ 方向，ξ=0）
#  12-15边中点（沿 η 方向，η=0）
#  16-19边中点（沿 ζ 方向，ζ=0）
_HEX20 = [
    (-1, -1, -1, 'c'), (1, -1, -1, 'c'), (1, 1, -1, 'c'), (-1, 1, -1, 'c'),
    (-1, -1, 1, 'c'), (1, -1, 1, 'c'), (1, 1, 1, 'c'), (-1, 1, 1, 'c'),
    (0, -1, -1, 'x'), (0, 1, -1, 'x'), (0, -1, 1, 'x'), (0, 1, 1, 'x'),
    (-1, 0, -1, 'y'), (1, 0, -1, 'y'), (-1, 0, 1, 'y'), (1, 0, 1, 'y'),
    (-1, -1, 0, 'z'), (1, -1, 0, 'z'), (1, 1, 0, 'z'), (-1, 1, 0, 'z'),
]


def _hex20_shape(nx_n, ny_n, nz_n, typ, gx, gy, gz):
    """单节点形函数 N 及其对自然坐标的导数（∂N/∂ξ,∂N/∂η,∂N/∂ζ）。"""
    if typ == 'c':
        P = (1 + nx_n * gx) * (1 + ny_n * gy) * (1 + nz_n * gz)
        Q = (nx_n * gx + ny_n * gy + nz_n * gz - 2.0)
        N = 0.125 * P * Q
        dxi = 0.125 * nx_n * ((1 + ny_n * gy) * (1 + nz_n * gz) * Q + P)
        deta = 0.125 * ny_n * ((1 + nx_n * gx) * (1 + nz_n * gz) * Q + P)
        dze = 0.125 * nz_n * ((1 + nx_n * gx) * (1 + ny_n * gy) * Q + P)
    elif typ == 'x':  # ξ=0 边中点
        N = 0.25 * (1 - gx * gx) * (1 + ny_n * gy) * (1 + nz_n * gz)
        dxi = 0.25 * (-2 * gx) * (1 + ny_n * gy) * (1 + nz_n * gz)
        deta = 0.25 * (1 - gx * gx) * ny_n * (1 + nz_n * gz)
        dze = 0.25 * (1 - gx * gx) * (1 + ny_n * gy) * nz_n
    elif typ == 'y':  # η=0 边中点
        N = 0.25 * (1 + nx_n * gx) * (1 - gy * gy) * (1 + nz_n * gz)
        dxi = 0.25 * nx_n * (1 - gy * gy) * (1 + nz_n * gz)
        deta = 0.25 * (1 + nx_n * gx) * (-2 * gy) * (1 + nz_n * gz)
        dze = 0.25 * (1 + nx_n * gx) * (1 - gy * gy) * nz_n
    else:  # 'z' ζ=0 边中点
        N = 0.25 * (1 + nx_n * gx) * (1 + ny_n * gy) * (1 - gz * gz)
        dxi = 0.25 * nx_n * (1 + ny_n * gy) * (1 - gz * gz)
        deta = 0.25 * (1 + nx_n * gx) * ny_n * (1 - gz * gz)
        dze = 0.25 * (1 + nx_n * gx) * (1 + ny_n * gy) * (-2 * gz)
    return N, dxi, deta, dze


def _build_B(dNdx: np.ndarray) -> np.ndarray:
    """由 dN/dx 构造 6×3n 应变-位移矩阵 B（ε = B·u），对任意节点数通用。"""
    n = dNdx.shape[0]
    B = np.zeros((6, 3 * n))
    for a in range(n):
        B[0, 3 * a] = dNdx[a, 0]      # εxx ← ∂u/∂x
        B[1, 3 * a + 1] = dNdx[a, 1]  # εyy ← ∂v/∂y
        B[2, 3 * a + 2] = dNdx[a, 2]  # εzz ← ∂w/∂z
        B[3, 3 * a] = dNdx[a, 1]
        B[3, 3 * a + 1] = dNdx[a, 0]  # γxy = ∂u/∂y + ∂v/∂x
        B[4, 3 * a + 1] = dNdx[a, 2]
        B[4, 3 * a + 2] = dNdx[a, 1]  # γyz = ∂v/∂z + ∂w/∂y
        B[5, 3 * a] = dNdx[a, 2]
        B[5, 3 * a + 2] = dNdx[a, 0]  # γzx = ∂u/∂z + ∂w/∂x
    return B


@dataclass
class _ElasMat:
    """各向同性线弹性材料（Lamé 参数）。"""
    E: float
    nu: float

    @property
    def lam(self) -> float:
        return self.E * self.nu / ((1.0 + self.nu) * (1.0 - 2.0 * self.nu))

    @property
    def mu(self) -> float:
        return self.E / (2.0 * (1.0 + self.nu))

    def D(self) -> np.ndarray:
        """6×6 弹性矩阵 D（应力 = D·应变）。"""
        lam, mu = self.lam, self.mu
        D = np.zeros((6, 6))
        D[0, 0] = D[1, 1] = D[2, 2] = lam + 2.0 * mu
        D[0, 1] = D[0, 2] = D[1, 0] = D[1, 2] = D[2, 0] = D[2, 1] = lam
        D[3, 3] = D[4, 4] = D[5, 5] = mu
        return D


# 3×3×3 高斯积分点与权重（精确至四次项）
_GP3 = [-0.7745966692414834, 0.0, 0.7745966692414834]
_GW3 = [0.5555555555555556, 0.8888888888888888, 0.5555555555555556]


def hex20_stiffness(dx: float, dy: float, dz: float, mat: _ElasMat) -> np.ndarray:
    """
    参考二十节点六面体单元刚度矩阵（60×60）。
    对均匀结构化网格，所有单元几何相同，只需算一次后按自由度散射。
    """
    # 参考单元角点物理坐标（中心在原点）
    Xc = np.zeros((20, 3))
    for a, (xn, yn, zn, _) in enumerate(_HEX20):
        Xc[a] = [xn * dx / 2.0, yn * dy / 2.0, zn * dz / 2.0]

    D = mat.D()
    Ke = np.zeros((60, 60))

    for xi in _GP3:
        for eta in _GP3:
            for ze in _GP3:
                N = np.zeros(20)
                dN = np.zeros((20, 3))
                for a, (xn, yn, zn, t) in enumerate(_HEX20):
                    N[a], dxi, deta, dze = _hex20_shape(xn, yn, zn, t, xi, eta, ze)
                    dN[a] = [dxi, deta, dze]
                J = dN.T @ Xc
                detJ = np.linalg.det(J)
                invJ = np.linalg.inv(J)
                dNdx = dN @ invJ
                B = _build_B(dNdx)
                wgt = _GW3[_GP3.index(xi)] * _GW3[_GP3.index(eta)] * _GW3[_GP3.index(ze)]
                Ke += B.T @ D @ B * detJ * wgt
    return Ke


# ============================================================
#  ② 结构化二十节点六面体网格
# ============================================================
def brick_mesh20(L: float, b: float, h: float, nx: int, ny: int, nz: int):
    """
    均匀二十节点六面体砖块网格（梁：x=长度 L，截面 y=b（宽），z=h（高））。
    Returns:
        nodes : (nN,3) 节点坐标
        eles  : (nE,20) 单元连通（局部序见 _HEX20）
        gc    : 角点全局索引函数 gc(i,j,k)
    """
    Nx, Ny, Nz = nx + 1, ny + 1, nz + 1
    xs = np.linspace(0.0, L, Nx)
    ys = np.linspace(-b / 2.0, b / 2.0, Ny)
    zs = np.linspace(-h / 2.0, h / 2.0, Nz)

    nC = Nx * Ny * Nz
    nX = nx * Ny * Nz
    nY = Nx * ny * Nz
    nZ = Nx * Ny * nz
    nTot = nC + nX + nY + nZ

    nodes = np.zeros((nTot, 3))

    def gc(i, j, k):
        return i + j * Nx + k * Nx * Ny

    def gxe(i, j, k):
        return nC + (i + j * nx + k * nx * Ny)

    def gye(i, j, k):
        return nC + nX + (i + j * Nx + k * Nx * ny)

    def gze(i, j, k):
        return nC + nX + nY + (i + j * Nx + k * Nx * Ny)

    for k in range(Nz):
        for j in range(Ny):
            for i in range(Nx):
                nodes[gc(i, j, k)] = [xs[i], ys[j], zs[k]]
    for k in range(Nz):
        for j in range(Ny):
            for i in range(nx):
                nodes[gxe(i, j, k)] = [(xs[i] + xs[i + 1]) / 2.0, ys[j], zs[k]]
    for k in range(Nz):
        for j in range(ny):
            for i in range(Nx):
                nodes[gye(i, j, k)] = [xs[i], (ys[j] + ys[j + 1]) / 2.0, zs[k]]
    for k in range(nz):
        for j in range(Ny):
            for i in range(Nx):
                nodes[gze(i, j, k)] = [xs[i], ys[j], (zs[k] + zs[k + 1]) / 2.0]

    eles = []
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                conn = [
                    gc(i, j, k), gc(i + 1, j, k), gc(i + 1, j + 1, k), gc(i, j + 1, k),
                    gc(i, j, k + 1), gc(i + 1, j, k + 1), gc(i + 1, j + 1, k + 1), gc(i, j + 1, k + 1),
                    gxe(i, j, k), gxe(i, j + 1, k), gxe(i, j, k + 1), gxe(i, j + 1, k + 1),
                    gye(i, j, k), gye(i + 1, j, k), gye(i, j, k + 1), gye(i + 1, j, k + 1),
                    gze(i, j, k), gze(i + 1, j, k), gze(i + 1, j + 1, k), gze(i, j + 1, k),
                ]
                eles.append(conn)
    return nodes, np.array(eles), gc


# ============================================================
#  ③ 装配 + 求解
# ============================================================
def _assemble(nodes, eles, Ke_ref):
    """将参考单元刚度按自由度散射装配为全局刚度（COO，自动叠加共享节点）。"""
    nN = nodes.shape[0]
    nE = eles.shape[0]
    dofs = np.repeat(eles, 3, axis=1) * 3 + np.tile(np.arange(3), eles.shape[1])
    rr = np.repeat(dofs, dofs.shape[1], axis=1).ravel()
    cc = np.tile(dofs, dofs.shape[1]).ravel()
    vv = np.tile(Ke_ref.ravel(), nE)
    K = coo_matrix((vv, (rr, cc)), shape=(3 * nN, 3 * nN)).tocsr()
    return K


def _solve(K, F, fixed_dofs):
    """消除法施加约束并求解，返回完整位移向量（约束处为 0）。"""
    nD = K.shape[0]
    free = np.array(sorted(set(range(nD)) - set(fixed_dofs)))
    Kff = K[free][:, free]
    Ff = F[free]
    uf = spsolve(Kff, Ff)
    u = np.zeros(nD)
    u[free] = uf
    return u


def solve_cantilever(L, b, h, E, nu, P, nx=10, ny=3, nz=3):
    """
    悬臂梁：x=0 固定，自由端 x=L 施加集中力 P（沿 -z，即截面薄边方向，
    挠度最明显）。自由端挠度（中点）对标解析解 δ = P·L³ / (3·E·I)，
    I = h³·b/12（绕 y 轴弯曲，h 为薄边高度、b 为宽度）。
    Returns: (u_full, tip_disp_z, None)
    """
    mat = _ElasMat(E, nu)
    nodes, eles, gc = brick_mesh20(L, b, h, nx, ny, nz)
    dx, dy, dz = L / nx, b / ny, h / nz
    Ke_ref = hex20_stiffness(dx, dy, dz, mat)

    Nx, Ny, Nz = nx + 1, ny + 1, nz + 1
    nN = nodes.shape[0]
    K = _assemble(nodes, eles, Ke_ref)

    fixed = []
    for j in range(Ny):
        for k in range(Nz):
            g = gc(0, j, k)
            fixed += [3 * g, 3 * g + 1, 3 * g + 2]

    F = np.zeros(3 * nN)
    end_nodes = [gc(nx, j, k) for j in range(Ny) for k in range(Nz)]
    f_per = -P / len(end_nodes)
    for g in end_nodes:
        F[3 * g + 2] += f_per

    u = _solve(K, F, fixed)

    tip_g = gc(nx, Ny // 2, Nz // 2)
    tip_disp = u[3 * tip_g + 2]
    return u, tip_disp, None


def solve_tension(L, b, h, E, nu, P, nx=8, ny=2, nz=2):
    """
    轴向拉伸：x=0 固定，x=L 端面施加轴向拉力 P（+x）。
    对标解析解：δ = P·L / (E·A)，A = b·h；均匀轴向应力 σ = P/A。
    Returns: (u_full, tip_disp_x)
    """
    mat = _ElasMat(E, nu)
    nodes, eles, gc = brick_mesh20(L, b, h, nx, ny, nz)
    dx, dy, dz = L / nx, b / ny, h / nz
    Ke_ref = hex20_stiffness(dx, dy, dz, mat)

    Nx, Ny, Nz = nx + 1, ny + 1, nz + 1
    nN = nodes.shape[0]
    K = _assemble(nodes, eles, Ke_ref)

    fixed = []
    for j in range(Ny):
        for k in range(Nz):
            g = gc(0, j, k)
            fixed += [3 * g, 3 * g + 1, 3 * g + 2]

    F = np.zeros(3 * nN)
    end_nodes = [gc(nx, j, k) for j in range(Ny) for k in range(Nz)]
    f_per = P / len(end_nodes)
    for g in end_nodes:
        F[3 * g] += f_per

    u = _solve(K, F, fixed)
    tip_g = gc(nx, Ny // 2, Nz // 2)
    tip_disp = u[3 * tip_g]
    return u, tip_disp


# ============================================================
#  ④ 蒙特卡洛标定
# ============================================================
def calibrate_3d_cantilever(material_key: str = "steel",
                            n_cases: int = 20,
                            mesh: Tuple[int, int, int] = (10, 3, 3),
                            seed: int = 5000) -> CalibrationResult:
    """悬臂梁 3D 实体有限元 vs 欧拉-伯努利解析解（δ=PL³/3EI）。"""
    rng = np.random.RandomState(seed)
    mat = MATERIALS[material_key]
    E, nu = mat.E, mat.nu

    ana_vals, num_vals = [], []
    t0 = time.perf_counter()
    for _ in range(n_cases):
        L = rng.uniform(0.5, 2.0)
        b = rng.uniform(0.02, 0.06)
        h = rng.uniform(0.01, 0.04)
        P = rng.uniform(500, 8000)
        # 绕 y 轴弯曲（载荷沿薄边 z 方向）：I = h³·b/12
        I = h ** 3 * b / 12.0
        ana = P * L ** 3 / (3.0 * E * I)
        _, tip, _ = solve_cantilever(L, b, h, E, nu, P, *mesh)
        ana_vals.append(ana)
        num_vals.append(abs(tip))

    elapsed = time.perf_counter() - t0
    ana_arr = np.array(ana_vals)
    num_arr = np.array(num_vals)
    rel = np.abs(num_arr - ana_arr) / np.where(ana_arr > 1e-15, ana_arr, 1.0) * 100.0
    mean_err = float(np.mean(rel))
    return CalibrationResult(
        scenario="beam_3d_cantilever_hex20",
        analytical_baseline=float(np.mean(ana_arr)),
        numerical_mean=float(np.mean(num_arr)),
        numerical_std=float(np.std(num_arr)),
        relative_error_pct=round(mean_err, 3),
        cv_pct=round(float(np.std(num_arr) / np.mean(num_arr) * 100) if np.mean(num_arr) > 0 else 0, 3),
        meets_caliber=mean_err <= 2.0,
        n_runs=n_cases,
        wall_time_s=round(elapsed, 3),
    )


def calibrate_3d_tension(material_key: str = "steel",
                         n_cases: int = 20,
                         mesh: Tuple[int, int, int] = (8, 2, 2),
                         seed: int = 6000) -> CalibrationResult:
    """轴向拉伸 3D 实体有限元 vs 解析解（δ=PL/EA，σ=P/A）。"""
    rng = np.random.RandomState(seed)
    mat = MATERIALS[material_key]
    E, nu = mat.E, mat.nu

    ana_vals, num_vals = [], []
    t0 = time.perf_counter()
    for _ in range(n_cases):
        L = rng.uniform(0.3, 1.5)
        b = rng.uniform(0.02, 0.08)
        h = rng.uniform(0.02, 0.06)
        P = rng.uniform(500, 8000)
        A = b * h
        ana = P * L / (E * A)
        _, tip = solve_tension(L, b, h, E, nu, P, *mesh)
        ana_vals.append(ana)
        num_vals.append(abs(tip))

    elapsed = time.perf_counter() - t0
    ana_arr = np.array(ana_vals)
    num_arr = np.array(num_vals)
    rel = np.abs(num_arr - ana_arr) / np.where(ana_arr > 1e-15, ana_arr, 1.0) * 100.0
    mean_err = float(np.mean(rel))
    # 3D 实体单元对标轴向拉伸闭式解的残差来自端面圣维南效应 + 等效节点力集总，
    # 亚 1% 即属「标尺级」精度（区别于 P2 中 1D 梁/Hermite 的精确 ±0.5%）。
    return CalibrationResult(
        scenario="beam_3d_tension_hex20",
        analytical_baseline=float(np.mean(ana_arr)),
        numerical_mean=float(np.mean(num_arr)),
        numerical_std=float(np.std(num_arr)),
        relative_error_pct=round(mean_err, 3),
        cv_pct=round(float(np.std(num_arr) / np.mean(num_arr) * 100) if np.mean(num_arr) > 0 else 0, 3),
        meets_caliber=mean_err <= 1.0,
        n_runs=n_cases,
        wall_time_s=round(elapsed, 3),
    )


def run_fem3d_calibration(material_key: str = "steel") -> Dict[str, CalibrationResult]:
    """执行 3D 实体有限元全部标定场景。"""
    results = {}
    results["beam_3d_tension_hex20"] = calibrate_3d_tension(material_key)
    results["beam_3d_cantilever_hex20"] = calibrate_3d_cantilever(material_key)
    return results


# ============================================================
#  ⑤ 三维变形可视化（Plotly，懒加载）
# ============================================================
def deformed_mesh_plotly(L, b, h, E, nu, P, nx=12, ny=4, nz=4,
                         deform_scale: Optional[float] = None):
    """
    返回 Plotly 3D 图：灰色=未变形网格，蓝色=变形后（悬臂梁向下弯曲）。
    用于 Demo 「装备级 CAE · 3D 实体」面板直观展示自研求解器的变形结果。
    """
    import plotly.graph_objects as go  # 懒加载，求解器本身不依赖 plotly

    nodes, eles, gc = brick_mesh20(L, b, h, nx, ny, nz)
    u, tip, _ = solve_cantilever(L, b, h, E, nu, P, nx, ny, nz)

    max_disp = float(np.max(np.abs(u)))
    if deform_scale is None:
        deform_scale = (0.25 * L / max_disp) if max_disp > 1e-12 else 0.0
    disp = u.reshape(-1, 3) * deform_scale
    nodes_def = nodes + disp

    # 12 条六面体棱边（角点局部索引 0-7 与 Hex8 一致）
    edges = [(0, 1), (1, 2), (2, 3), (3, 0),
             (4, 5), (5, 6), (6, 7), (7, 4),
             (0, 4), (1, 5), (2, 6), (3, 7)]

    def _segs(coords):
        xs, ys, zs = [], [], []
        for e in eles:
            for (a, bb) in edges:
                p0, p1 = coords[e[a]], coords[e[bb]]
                xs += [p0[0], p1[0], None]
                ys += [p0[1], p1[1], None]
                zs += [p0[2], p1[2], None]
        return xs, ys, zs

    ux, uy, uz = _segs(nodes)
    dx_, dy_, dz_ = _segs(nodes_def)

    fig = go.Figure()
    fig.add_trace(go.Scatter3d(x=ux, y=uy, z=uz, mode="lines",
                               line=dict(color="lightgray", width=2),
                               name="未变形", hoverinfo="skip"))
    fig.add_trace(go.Scatter3d(x=dx_, y=dy_, z=dz_, mode="lines",
                               line=dict(color="#185fa5", width=3),
                               name="变形后", hoverinfo="skip"))
    fig.update_layout(
        height=420, margin=dict(l=0, r=0, t=30, b=0),
        title=f"悬臂梁 3D 实体有限元变形（Hex20 二次单元）｜ 自由端挠度 {abs(tip)*1e3:.2f} mm",
        scene=dict(xaxis_title="x (长度)", yaxis_title="y (宽)", zaxis_title="z (高)",
                   aspectmode="data"),
        legend=dict(orientation="h", y=1.02),
    )
    return fig


# ============================================================
#  ⑥ 自检
# ============================================================
def run_demo() -> None:
    print("=" * 70)
    print("  P2-C 3D 实体有限元 · 自检标定报告（Hex20 二次单元，对标 ANSYS SOLID186）")
    print("=" * 70)
    print(f"  数值方法: 二十节点二次六面体 + 3×3×3 高斯 (numpy + scipy.sparse)")
    print(f"  金标准:   解析解（欧拉-伯努利 / 轴向拉伸闭式）")
    print("-" * 70)

    results = run_fem3d_calibration()
    all_pass = True
    for key, res in results.items():
        status = "PASS" if res.meets_caliber else "FAIL"
        if not res.meets_caliber:
            all_pass = False
        print(f"\n  [{status}] {res.scenario}")
        print(f"    解析基线 : {res.analytical_baseline:.6e}")
        print(f"    数值均值 : {res.numerical_mean:.6e} ± {res.numerical_std:.6e}")
        print(f"    相对误差 : {res.relative_error_pct:.3f}%")
        print(f"    工况数   : {res.n_runs}  耗时: {res.wall_time_s}s")

    print("\n" + "=" * 70)
    overall = "ALL PASS" if all_pass else "SOME FAIL"
    print(f"  总体判定: {overall}  ({len(results)} 场景)")
    if all_pass:
        print("  >>> P2_FEM3D_OK <<<")
    print("=" * 70)


if __name__ == "__main__":
    run_demo()
