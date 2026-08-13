# P1 W1 开工脚手架 · 几何内核与实时数据底座

> 配套《P1 启动包 v1.0》。本目录是 P1 第一周（W1）可立即执行的工程起点。
> 生成日期：2026-08-07；v1.1 更正：OGG 已开源，注册免费 Gitee 账号即可 clone，无需公测申请（"公测招募"为可选增强计划）。

## 1. 仓库澄清（务必先看，避免走错仓库）

本项目锁定的几何内核是 **华为/DISA 的 OGG（OpenGeometry Group）**，但互联网上存在一个**同名不同源**的项目，极易混淆：

| 项目 | 地址 | 语言/技术 | 许可证 | 是否本项目所需 |
|---|---|---|---|---|
| 华为/DISA OGG（目标） | gitee.com/opengeometry | C++（Fork 自 OCCT） | LGPL 2.1 | ✅ 是 |
| OpenGeometry-io（同名混淆） | github.com/OpenGeometry-io | Rust→WASM（浏览器 CAD） | MPL-2.0 | ❌ 否 |

**结论：不要去 GitHub 搜 "OpenGeometry"，那是另一个同名项目。华为 OGG 在 Gitee（gitee.com/opengeometry），注册免费 Gitee 账号即可 clone，无需申请。**

## 2. OGG 源码获取（注册 Gitee 账号即可 clone）

OGG 已开源（LGPL 2.1），**注册免费 Gitee 账号即可直接 clone / 下载 ZIP，无审批环节**：

- [ ] 注册 Gitee 账号（免费）：https://gitee.com/signup
- [ ] clone 仓库：`git clone https://gitee.com/opengeometry/OGG.git`（或下载 ZIP）
- [ ] 内部 Git 镜像归档（避免外部依赖/中断）
- [ ] 记录实际获取版本号（master / ogg_202405 / OCCT-7.6 等）与 LICENSE（LGPL 2.1）
- [ ] （可选）参与官网 opengeometry.cn 的"公测招募"——这是华为 486 项增强特性的早期验证志愿计划，非获取代码门槛

> **本地镜像已就位（2026-08-07 核实）**：本脚手架 `ogg_src/` 目录已包含 OGG **master** 分支完整源码（commit `d90800a`，2024-05-06，LGPL 2.1，66388 文件），无需再 clone，注册 Gitee 账号即可直接获取。一键构建见 `build_ogg.sh`。

许可证提醒：OGG 继承 OCCT 的 **LGPL 2.1**——动态链接可闭源分发你的应用，但**修改 OGG/OCCT 库本身须开源**。商用前请法务确认分发方式。

## 3. OCCT 作为上游保底（API 兼容）

OGG 与 OCCT 同源（OGG Fork 自 OCCT），API 高度兼容。可直接以 OGG 为基础开发；若 OGG 分支不稳定，OCCT 作为保底上游，切换成本主要在构建系统。

- OCCT 官方仓库：github.com/Open-Cascade-SAS/OCCT（LGPL 2.1，直接 clone，无需申请）
- OGG 被设计为 OCCT 的 drop-in replacement，API 高度兼容 → 切换成本主要在构建系统（CMake 目标名/头路径）
- 本脚手架的 Dockerfile / CMake / 验证程序均以 OCCT 为基准编写，OGG 到位后替换依赖源即可

## 4. 环境搭建

- 构建镜像：见 `Dockerfile`（Ubuntu 22.04 + 编译链 + OCCT 依赖 Tcl/Tk、FreeType、TBB）
- 容器编排：见 `docker-compose.yml`（geometry-core 服务 + 时序库 timeseries 占位，为数据底座预留）
- 构建机上本地构建 OCCT（非本沙箱执行）：
  ```
  git clone https://github.com/Open-Cascade-SAS/OCCT.git
  cd OCCT && mkdir build && cd build
  cmake -DCMAKE_BUILD_TYPE=Release .. && make -j$(nproc)
  ```

## 5. 最小验证程序

`hello_geometry.cpp` + `CMakeLists.txt`：生成一个实体（盒体），统计拓扑（面/边），导出 STEP。编译运行通过即证明几何链路可用。

```
mkdir build && cd build
cmake .. && make
./hello_geometry out.step
```

## 6. 下一步触发条件（真实编译/部署）

以下就绪后即可执行真实构建与 OGG 源码接入：
1. P0 门禁拍板：部署模式（云/私有化+边缘）、预算、场景边界
2. OGG 仓库已 clone（或确认先以 OCCT 推进）
3. 提供构建机（Linux，≥8 核/16G）或华为云 ECS 账号
