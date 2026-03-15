cmake_minimum_required(VERSION 3.18)
project(autotopology_cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(pybind11 REQUIRED)

pybind11_add_module(autotopology_cpp
    bindings.cpp
    src/stub.cpp
)

target_include_directories(autotopology_cpp PRIVATE include)
