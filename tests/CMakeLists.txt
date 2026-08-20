add_custom_target(telemetry_tests)

add_test(NAME clang_bootstrap_preset_configures
    COMMAND ${CMAKE_COMMAND}
        -DREPO_ROOT=${CMAKE_SOURCE_DIR}
        -P ${CMAKE_CURRENT_SOURCE_DIR}/toolchain/verify_clang_bootstrap_preset.cmake
)

add_test(NAME clang_bootstrap_core_builds
    COMMAND ${CMAKE_COMMAND}
        --build ${CMAKE_BINARY_DIR}
        --target telemetry_core
)

add_test(NAME clang_bootstrap_nats_adapter_builds
    COMMAND ${CMAKE_COMMAND}
        --build ${CMAKE_BINARY_DIR}
        --target nats_adapter
)

add_test(NAME clang_bootstrap_postgres_adapter_builds
    COMMAND ${CMAKE_COMMAND}
        --build ${CMAKE_BINARY_DIR}
        --target postgres_adapter
)

add_test(NAME clang_bootstrap_ingestor_builds
    COMMAND ${CMAKE_COMMAND}
        --build ${CMAKE_BINARY_DIR}
        --target ingestor
)

set(telemetry_runtime_test_modes "Debug")
if(TELEMETRY_ENABLE_ASAN OR TELEMETRY_ENABLE_UBSAN OR TELEMETRY_ENABLE_TSAN OR TELEMETRY_ENABLE_COVERAGE)
    set(telemetry_runtime_test_modes "Debug;RelWithDebInfo")
endif()

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

        if(relative_source MATCHES "^integration/nats/")
            target_link_libraries(${test_target}
                PRIVATE
                    telemetry::nats_adapter
            )
        elseif(relative_source MATCHES "^integration/postgres/")
            target_link_libraries(${test_target}
                PRIVATE
                    telemetry::postgres_adapter
            )
        endif()

        telemetry_enable_instrumentation(${test_target})
        add_dependencies(telemetry_tests ${test_target})

        if(CMAKE_BUILD_TYPE IN_LIST telemetry_runtime_test_modes)
            add_test(NAME ${test_target} COMMAND $<TARGET_FILE:${test_target}>)
            set_tests_properties(${test_target} PROPERTIES
                FIXTURES_REQUIRED telemetry_test_binaries
            )
        endif()
    endforeach()
endfunction()

telemetry_register_discovered_tests(unit)
telemetry_register_discovered_tests(integration)
telemetry_register_discovered_tests(system)

add_test(NAME ingestor_prints_version
    COMMAND $<TARGET_FILE:ingestor>
)
set_tests_properties(ingestor_prints_version PROPERTIES
    PASS_REGULAR_EXPRESSION "0\\.1\\.0"
)

if(CMAKE_BUILD_TYPE IN_LIST telemetry_runtime_test_modes)
    add_test(
        NAME telemetry_build_tests
        COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR} --target telemetry_tests
    )
    set_tests_properties(telemetry_build_tests PROPERTIES
        FIXTURES_SETUP telemetry_test_binaries
    )
endif()

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