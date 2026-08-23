# cpp/src/adapters/nats/CMakeLists.txt
add_library(nats_adapter STATIC
    nats_adapter.cpp
)

add_library(telemetry::nats_adapter ALIAS nats_adapter)

target_link_libraries(nats_adapter
    PUBLIC
        telemetry::core
)

target_include_directories(nats_adapter
    PUBLIC
        ${CMAKE_SOURCE_DIR}/cpp/include
)

telemetry_enable_warnings(nats_adapter)
telemetry_enable_instrumentation(nats_adapter)