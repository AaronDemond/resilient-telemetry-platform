add_executable(telemetry_benchmarks
    placeholder_bench.cpp
)

target_link_libraries(telemetry_benchmarks
    PRIVATE
        telemetry::core
)