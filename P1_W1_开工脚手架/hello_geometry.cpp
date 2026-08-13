// 最小 OCCT 几何链路验证：生成盒体 → 统计拓扑 → 导出 STEP
// 编译依赖 OCCT 开发包（或 OGG，API 兼容，drop-in replacement）
#include <BRepPrimAPI_MakeBox.hxx>
#include <TopExp_Explorer.hxx>
#include <TopoDS_Shape.hxx>
#include <TopAbs_ShapeEnum.hxx>
#include <STEPControl_Writer.hxx>
#include <Interface_Static.hxx>
#include <iostream>

int main(int argc, char** argv) {
    const char* out = (argc > 1) ? argv[1] : "out.step";

    // 1. 生成一个 100 x 60 x 40 的实体盒（单位 mm，对应几何误差标尺场景）
    TopoDS_Shape box = BRepPrimAPI_MakeBox(100.0, 60.0, 40.0).Shape();

    // 2. 统计拓扑：面(Face)与边(Edge)
    int faces = 0, edges = 0;
    for (TopExp_Explorer ex(box, TopAbs_FACE); ex.More(); ex.Next()) faces++;
    for (TopExp_Explorer ex(box, TopAbs_EDGE); ex.More(); ex.Next()) edges++;
    std::cout << "[OK] 生成实体盒，面数=" << faces << " 边数=" << edges << std::endl;

    // 3. 导出 STEP（验证 CAD 数据交换链路）
    STEPControl_Writer writer;
    writer.Transfer(box, STEPControl_AsIs);
    IFSelect_ReturnStatus st = writer.Write(out);
    if (st == IFSelect_RetDone) {
        std::cout << "[OK] 已导出 STEP: " << out << std::endl;
        return 0;
    }
    std::cerr << "[ERR] STEP 导出失败 (status=" << st << ")" << std::endl;
    return 1;
}
