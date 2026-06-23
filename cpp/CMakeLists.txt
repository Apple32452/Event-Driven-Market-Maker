cmake_minimum_required(VERSION 3.16)

project(market_making_cpp)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(market_making_benchmark src/benchmark.cpp)

if(CMAKE_CXX_COMPILER_ID MATCHES "AppleClang|Clang|GNU")
    target_compile_options(market_making_benchmark PRIVATE -O3)
endif()
