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
        "Windows Clang builds must use the clang-cl driver with an MSVC-compatible vcpkg triplet. "
        "The GNU-style clang++ driver is incompatible with MSVC-linked vcpkg packages.")
endif()

include(cmake/TelemetryInstrumentation.cmake)

find_package(Protobuf CONFIG REQUIRED)

set(PROTO_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/proto")
set(PROTO_CPP_GENERATED_DIR "${CMAKE_CURRENT_BINARY_DIR}/generated/cpp")
set(PROTO_PY_GENERATED_DIR "${CMAKE_CURRENT_BINARY_DIR}/generated/python")

set(PROTO_FILES
    ${PROTO_SOURCE_DIR}/telemetry/v1/envelope.proto
    ${PROTO_SOURCE_DIR}/telemetry/v1/operator_request.proto
    ${PROTO_SOURCE_DIR}/telemetry/v1/request_acknowledgement.proto
    ${PROTO_SOURCE_DIR}/telemetry/v1/standard_error.proto
    ${PROTO_SOURCE_DIR}/telemetry/v1/telemetry_event.proto
)

file(MAKE_DIRECTORY
    "${PROTO_CPP_GENERATED_DIR}"
    "${PROTO_PY_GENERATED_DIR}"
)

set_source_files_properties(${PROTO_FILES} PROPERTIES HEADER_FILE_ONLY TRUE)

add_library(telemetry_protos STATIC ${PROTO_FILES})
add_library(telemetry::protos ALIAS telemetry_protos)

protobuf_generate(
    TARGET telemetry_protos
    LANGUAGE cpp
    IMPORT_DIRS "${PROTO_SOURCE_DIR}"
    PROTOC_OUT_DIR "${PROTO_CPP_GENERATED_DIR}"
)

protobuf_generate(
    LANGUAGE python
    OUT_VAR PROTO_PY_SRCS
    PROTOS ${PROTO_FILES}
    IMPORT_DIRS "${PROTO_SOURCE_DIR}"
    PROTOC_OUT_DIR "${PROTO_PY_GENERATED_DIR}"
)

add_custom_target(telemetry_proto_python ALL DEPENDS ${PROTO_PY_SRCS})

target_include_directories(telemetry_protos SYSTEM
    PUBLIC
        $<BUILD_INTERFACE:${PROTO_CPP_GENERATED_DIR}>
)

target_link_libraries(telemetry_protos
    PUBLIC
        protobuf::libprotobuf
)

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