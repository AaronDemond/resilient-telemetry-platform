add_executable(ingestor main.cpp)
add_executable(telemetry::ingestor ALIAS ingestor)


target_link_libraries(ingestor
    PRIVATE 
        telemetry::core
        telemetry::nats_adapter
        telemetry::postgres_adapter
        telemetry::protos
)

telemetry_enable_warnings(ingestor)
telemetry_enable_instrumentation(ingestor)