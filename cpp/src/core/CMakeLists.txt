# cpp/src/core/CMakeLists.txt
add_library(telemetry_core STATIC
    telemetry_data.cpp
    version.cpp
)

add_library(telemetry::core ALIAS telemetry_core)

target_link_libraries(telemetry_core
    PUBLIC
        telemetry::protos
)

target_include_directories(telemetry_core
    PUBLIC
        ${CMAKE_SOURCE_DIR}/cpp/include
)

target_compile_features(telemetry_core PUBLIC cxx_std_20)

telemetry_enable_warnings(telemetry_core)