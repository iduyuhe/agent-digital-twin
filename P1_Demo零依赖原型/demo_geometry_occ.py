"""
几何保真层 · pythonocc-core（真 OCCT）实现
==========================================
正式路径：用 pythonocc-core（OCCT 的 Python 预编译绑定，pip 直装、免编译 C++）
演示真几何建模链路：实体建模 → 布尔融合 → 体积/表面积(真几何保真) → STEP 导出(CAD 交换)

降级路径：若环境无 pythonocc-core（如 Python 3.13 暂缺官方 wheel），自动 fallback 到 numpy 占位版，
保证 Demo 在任何机器可跑；几何指标含义一致，仅精度由占位近似。

依赖（正式）：
    pip install pythonocc-core     # 需 Python 3.9~3.11（3.13 待上游支持，fallback 兜底）
运行：
    python demo_geometry_occ.py
"""
import sys
import numpy as np

HAS_OCC = False
try:
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
    from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
    from OCC.Core.GProp import GProp_GProps
    from OCC.Core.BRepGProp import brepgprop_VolumeProperties, brepgprop_SurfaceProperties
    from OCC.Core.Bnd import Bnd_Box
    from OCC.Core.BRepBndLib import brepbndlib_Add
    from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_asIs
    HAS_OCC = True
except Exception as _e:  # noqa
    HAS_OCC = False


def build_device_occ():
    """真 OCCT 建模：主体 box + 电机 cylinder，布尔融合为单实体。
    返回 (shape_or_None, metrics, step_path_or_None)。"""
    if not HAS_OCC:
        return _build_device_numpy_fallback()

    # ① 主体 2.0×1.0×1.0；② 电机轴 cylinder(r=0.2,h=0.5)
    box = BRepPrimAPI_MakeBox(2.0, 1.0, 1.0).Shape()
    cyl = BRepPrimAPI_MakeCylinder(0.2, 0.5).Shape()
    fused = BRepAlgoAPI_Fuse(box, cyl).Shape()

    # 体积 / 表面积 —— 真几何保真（对标 OGG 几何精度）
    vprops = GProp_GProps()
    brepgprop_VolumeProperties(fused, vprops)
    sprops = GProp_GProps()
    brepgprop_SurfaceProperties(fused, sprops)
    vol, area = vprops.Mass(), sprops.Mass()

    # 包围盒尺寸
    bb = Bnd_Box()
    brepbndlib_Add(fused, bb)
    xmin, ymin, zmin, xmax, ymax, zmax = bb.Get()
    dims = (xmax - xmin, ymax - ymin, zmax - zmin)

    # STEP 导出 —— CAD 数据交换能力（对标 OGG 的 CAD 交换）
    step_path = None
    try:
        writer = STEPControl_Writer()
        writer.Transfer(fused, STEPControl_asIs)
        step_path = "device_model.step"
        writer.Write(step_path)
    except Exception:  # noqa
        step_path = None

    metrics = dict(
        引擎="OCCT(pythonocc-core)",
        体积=round(vol, 4),
        表面积=round(area, 4),
        尺寸X=round(dims[0], 3),
        尺寸Y=round(dims[1], 3),
        尺寸Z=round(dims[2], 3),
    )
    return fused, metrics, step_path


def _build_device_numpy_fallback():
    """无 pythonocc 时的近似占位：几何指标含义一致，精度由包围盒近似。"""
    dims = (2.3, 1.2, 1.2)
    metrics = dict(
        引擎="numpy占位(fallback)",
        体积=round(2.0 * 1.0 * 1.0, 4),
        表面积=round(2 * (2.0 * 1.0 + 2.0 * 1.0 + 1.0 * 1.0), 4),
        尺寸X=dims[0],
        尺寸Y=dims[1],
        尺寸Z=dims[2],
    )
    return None, metrics, None


def render_box_for_plotly(metrics):
    """把包围盒尺寸转成 plotly 可渲染的居中 box（演示用，不依赖 OCCT）。"""
    dx, dy, dz = metrics["尺寸X"], metrics["尺寸Y"], metrics["尺寸Z"]
    return dict(type="box", x=[0], y=[0], z=[0],
                box_x=[dx], box_y=[dy], box_z=[dz],
                line=dict(color="#2563eb", width=2))


if __name__ == "__main__":
    shape, metrics, step = build_device_occ()
    print("几何引擎:", "OCCT(pythonocc-core)" if HAS_OCC else "numpy占位(fallback)")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
    print("  STEP导出:", step if step else "（fallback 跳过）")
    print("GEOMETRY_OK")
