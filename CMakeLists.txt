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

if(CMAKE_CXX_COMPILER_ID STREQUAL "Clang" AND
   CMAKE_CXX_SIMULATE_ID STREQUAL "MSVC" AND
   CMAKE_CXX_COMPILER_VERSION VERSION_LESS "19.0.0")
    message(FATAL_ERROR
        "Clang 19.0.0 or newer is required when using the MSVC STL. "
        "Found ${CMAKE_CXX_COMPILER_VERSION}. Upgrade LLVM or select a compatible standard library.")
endif()

if(WIN32 AND
   CMAKE_CXX_COMPILER_ID STREQUAL "Clang" AND
   NOT CMAKE_CXX_SIMULATE_ID STREQUAL "MSVC")
    message(FATAL_ERROR
        "Windows Clang builds must use the clang-cl driver with the x64-windows vcpkg triplet. "
        "The GNU-style clang++ driver is incompatible with MSVC-linked vcpkg packages.")
endif()

include(cmake/TelemetryInstrumentation.cmake)

if(NOT DEFINED VCPKG_TARGET_TRIPLET)
    set(VCPKG_TARGET_TRIPLET "x64-windows")
endif()

list(PREPEND CMAKE_PREFIX_PATH
    "${CMAKE_BINARY_DIR}/vcpkg_installed/${VCPKG_TARGET_TRIPLET}"
)

find_package(Protobuf CONFIG REQUIRED)

set(PROTO_FILES
    ${CMAKE_SOURCE_DIR}/proto/telemetry/v1/envelope.proto
    ${CMAKE_SOURCE_DIR}/proto/telemetry/v1/operator_request.proto
    ${CMAKE_SOURCE_DIR}/proto/telemetry/v1/request_acknowledgement.proto
    ${CMAKE_SOURCE_DIR}/proto/telemetry/v1/standard_error.proto
    ${CMAKE_SOURCE_DIR}/proto/telemetry/v1/telemetry_event.proto
)

set(PROTOBUF_GENERATE_CPP_APPEND_PATH ON)
protobuf_generate_cpp(PROTO_CPP_SRCS PROTO_CPP_HDRS ${PROTO_FILES})
protobuf_generate_python(PROTO_PY_SRCS ${PROTO_FILES})

add_custom_target(telemetry_proto_python ALL DEPENDS ${PROTO_PY_SRCS})

add_library(telemetry_protos STATIC ${PROTO_CPP_SRCS} ${PROTO_CPP_HDRS})
add_library(telemetry::protos ALIAS telemetry_protos)

target_include_directories(telemetry_protos
    PUBLIC
        ${CMAKE_BINARY_DIR}
)

target_link_libraries(telemetry_protos
    PUBLIC
        protobuf::libprotobuf
)

add_executable(telemetry_proto_compile_check
    cpp/tests/proto_compile_smoke.cpp
)

target_link_libraries(telemetry_proto_compile_check
    PRIVATE
        telemetry::protos
)

target_include_directories(telemetry_proto_compile_check
    PRIVATE
        ${CMAKE_BINARY_DIR}
)

telemetry_enable_warnings(telemetry_proto_compile_check)

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