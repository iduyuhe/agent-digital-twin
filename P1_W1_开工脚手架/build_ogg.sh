#!/usr/bin/env bash
# ============================================================================
# P1 W1 · OGG 一键构建 + 最小验证
# 用法：在 Linux 构建机或本仓库 Docker 容器内执行  ./build_ogg.sh
# 前置：ogg_src/ 已存在（git clone https://gitee.com/opengeometry/OGG.git ogg_src）
# 说明：OGG 与 OCCT 同源（Fork 自 OCCT），构建方式一致，均为 CMake。
# ============================================================================
set -e
cd "$(dirname "$0")"

SRC=ogg_src
if [ ! -d "$SRC" ]; then
  echo "ERROR: 未找到 $SRC/，请先执行："
  echo "  git clone --depth 1 --branch master https://gitee.com/opengeometry/OGG.git ogg_src"
  exit 1
fi

echo "=== [1/4] 检测源码版本 ==="
( cd "$SRC" && git log -1 --format="branch=%d commit=%H %ci" 2>/dev/null ) || echo "(非 git 或 detached)"
ls "$SRC"/LICENSE* 2>/dev/null | head

echo "=== [2/4] CMake 配置 ==="
mkdir -p build && cd build
cmake \
  -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_TYPE=Release \
  -DINSTALL_DIR="$(pwd)/../install" \
  -DUSE_TK=OFF \
  -DUSE_FREETYPE=ON \
  -DUSE_TBB=ON \
  "$SRC"

echo "=== [3/4] 编译（$(nproc) 核并行）==="
make -j"$(nproc)"

echo "=== [4/4] 安装到 ./install ==="
make install
echo "DONE. 产物位于 $(pwd)/../install"

echo ""
echo "=== 最小验证程序（hello_geometry）==="
cd "$(dirname "$0")"
mkdir -p build_demo && cd build_demo
cmake -DOGG_INSTALL_DIR="$(pwd)/../install" ..
make -j"$(nproc)"
./hello_geometry out.step
echo "验证完成：若见拓扑统计与 STEP 导出成功，几何链路可用。"
