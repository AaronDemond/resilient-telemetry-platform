cmake_minimum_required(VERSION 3.25)

project(resilient_telemetry_platform
    VERSION 0.1.0
    DESCRIPTION "Resilient telemetry and operations platform"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(TELEMETRY_ENABLE_ASAN "Enable AddressSanitizer" OFF)
option(TELEMETRY_ENABLE_UBSAN "Enable UndefinedBehaviorSanitizer" OFF)
option(TELEMETRY_ENABLE_TSAN "Enable ThreadSanitizer" OFF)
option(TELEMETRY_ENABLE_COVERAGE "Enable coverage instrumentation" OFF)
option(TELEMETRY_BUILD_FUZZERS "Build fuzz targets" OFF)
option(TELEMETRY_BUILD_BENCHMARKS "Build benchmark targets" OFF)

if(TELEMETRY_ENABLE_TSAN AND
   (TELEMETRY_ENABLE_ASAN OR TELEMETRY_ENABLE_UBSAN))
    message(FATAL_ERROR
        "TSan must use its own build; do not combine it with ASan/UBSan")
endif()

include(cmake/TelemetryInstrumentation.cmake)

add_subdirectory(cpp/src/core)
add_subdirectory(cpp/src/adapters/nats)
add_subdirectory(cpp/src/adapters/postgres)
add_subdirectory(cpp/apps/ingestor)
add_subdirectory(cpp/apps/operations_api)
add_subdirectory(cpp/apps/replay_tool)

include(CTest)
if(BUILD_TESTING)
    add_subdirectory(tests)
endif()