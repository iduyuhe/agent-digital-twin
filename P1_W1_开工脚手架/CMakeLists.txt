cmake_minimum_required(VERSION 3.16)
project(hello_geometry CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 查找 OCCT（或 OGG，API 兼容）；构建机需先安装 OCCT 开发包
find_package(OpenCASCADE REQUIRED)

add_executable(hello_geometry hello_geometry.cpp)
target_include_directories(hello_geometry PRIVATE ${OpenCASCADE_INCLUDE_DIRS})
target_link_libraries(hello_geometry ${OpenCASCADE_LIBRARIES})
