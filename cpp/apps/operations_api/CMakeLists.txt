add_executable(operations_api
    main.cpp
    units_api_v1.cpp
)
add_executable(telemetry::operations_api ALIAS operations_api)

target_link_libraries(operations_api
    PRIVATE
        telemetry::core
        telemetry::postgres_adapter
        Drogon::Drogon
        JsonCpp::JsonCpp
)

target_include_directories(operations_api
    PRIVATE
        ${CMAKE_SOURCE_DIR}/cpp/apps/operations_api
)

telemetry_enable_warnings(operations_api)
telemetry_enable_instrumentation(operations_api)