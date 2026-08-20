# cpp/apps/operations-api/CMakeLists.txt
add_executable(operations_api main.cpp)
add_executable(telemetry::operations_api ALIAS operations_api)

target_link_libraries(operations_api
    PRIVATE
        telemetry::core
        telemetry::postgres_adapter
)

telemetry_enable_instrumentation(operations_api)