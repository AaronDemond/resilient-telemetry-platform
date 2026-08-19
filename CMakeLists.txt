cmake_minimum_required(VERSION 3.25)
project(resilient_telemetry_platform
        VERSION 0.1.0
        DESCRIPTION "Resilient telemetry and operations platform"
        LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Later Phase 1 tasks add warnings, sanitizers, and vcpkg.
# Keep this file about targets and include paths.

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