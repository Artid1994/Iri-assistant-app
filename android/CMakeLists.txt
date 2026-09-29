# CMakeLists.txt for libjari_bridge.so
# Stage 21: JNI native library for HDC hypervector operations
cmake_minimum_required(VERSION 3.22.0)
project(jari_bridge VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# HDC hypervector dimension (must match Kotlin HV_DIM = 10000)
set(HV_DIM 10000)

# Source files - using correct paths under android/jni/src/
add_library(jari_bridge SHARED
    ${CMAKE_CURRENT_SOURCE_DIR}/jni/src/jari_bridge.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/jni/src/hv_encode.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/jni/src/hv_decode.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/jni/src/hv_similarity.cpp
)

# Include directories
target_include_directories(jari_bridge PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/jni/include
)

# Link against Android/log for debug output
find_library(log-lib log)
target_link_libraries(jari_bridge PRIVATE ${log-lib})

# Android 15 / API 35: 16KB page size alignment for native libraries
# Required for devices with 16KB page size (arm64-v8a with page_size=16384)
# Global linker flags ensure ALL .so files (including Chaquopy Python libs) are aligned
set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -Wl,-z,max-page-size=16384")
set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -Wl,-z,common-page-size=16384")

target_link_options(jari_bridge PRIVATE
    "-Wl,-z,max-page-size=16384"
    "-Wl,-z,common-page-size=16384"
)

# Export symbols for JNI
target_compile_definitions(jari_bridge PRIVATE
    HV_DIM=${HV_DIM}
    JNIEXPORT=__attribute__((visibility("default")))
)
