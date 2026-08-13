# P1 几何内核构建基础镜像
# 用途：预装 OCCT/OGG 编译链与依赖；OGG 到位后替换依赖源即可
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    g++ \
    clang \
    libtbb-dev \
    libfreetype6-dev \
    tcl-dev \
    tk-dev \
    libx11-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    pkg-config \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
# 注：OCCT/OGG 源码 clone 与编译留给构建机/CI 步骤，不在镜像构建期执行（镜像仅含工具链）
# 构建机执行示例：
#   git clone https://github.com/Open-Cascade-SAS/OCCT.git
#   cd OCCT && mkdir build && cd build && cmake -DCMAKE_BUILD_TYPE=Release .. && make -j$(nproc)

CMD ["/bin/bash"]
