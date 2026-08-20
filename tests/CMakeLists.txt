function(telemetry_register_discovered_tests test_root)
    file(GLOB_RECURSE discovered_test_sources CONFIGURE_DEPENDS
        "${CMAKE_CURRENT_SOURCE_DIR}/${test_root}/*_test.cpp"
    )

    foreach(test_source IN LISTS discovered_test_sources)
        file(RELATIVE_PATH relative_source
            "${CMAKE_CURRENT_SOURCE_DIR}"
            "${test_source}"
        )

        get_filename_component(test_name "${test_source}" NAME_WE)
        string(REPLACE "/" "_" test_target "${relative_source}")
        string(REPLACE "\\" "_" test_target "${test_target}")
        string(REPLACE "." "_" test_target "${test_target}")

        add_executable(${test_target} "${test_source}")
        target_link_libraries(${test_target}
            PRIVATE
                telemetry::core
        )
        telemetry_enable_instrumentation(${test_target})

        if(CMAKE_BUILD_TYPE STREQUAL "Debug")
            add_test(NAME ${test_target} COMMAND ${test_target})
        endif()
    endforeach()
endfunction()

telemetry_register_discovered_tests(unit)
telemetry_register_discovered_tests(integration)
telemetry_register_discovered_tests(system)

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
    telemetry_enable_instrumentation(telemetry_placeholder_fuzzer)
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
    telemetry_enable_instrumentation(telemetry_benchmarks)
endif()