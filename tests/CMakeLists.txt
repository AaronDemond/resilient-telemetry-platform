add_executable(telemetry_unit_tests
    unit/core/core_smoke_test.cpp
)

target_link_libraries(telemetry_unit_tests
    PRIVATE
        telemetry::core
)
    

option(TELEMETRY_BUILD_FUZZERS "Build libfuzer targets" OFF)

if(TELEMETRY_BUILD_FUZZERS)
    add_executable(telemetry_placeholder_fuzzer
        fuzz/placeholder_fuzzer.cpp
    )

    target_link_libraries(telemetry_placeholder_fuzzer
        PRIVATE
            telemetry::core
    )
    target_compile_options(telemetry_placeholder_fuzzer 
        PRIVATE -fsanitize=fuzzer)
    target_link_options(telemetry_placeholder_fuzzer 
        PRIVATE -fsanitize=fuzzer)
endif()

option(TELEMETRY_BUILD_BENCHMARKS "Build Google Benchmark targets" OFF)

if(TELEMETRY_BUILD_BENCHMARKS)
    add_executable(telemetry_benchmarks
        benchmark/placeholder_bench.cpp
    )
    target_link_libraries(telemetry_benchmarks
        PRIVATE
            telemetry::core
    )
endif()

