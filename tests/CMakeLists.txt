find_package(Python3 REQUIRED COMPONENTS Interpreter)

add_custom_target(telemetry_tests)
add_dependencies(telemetry_tests telemetry_proto_python)

if(WIN32)
    add_test(NAME clang_bootstrap_preset_configures
        COMMAND ${CMAKE_COMMAND}
            -DREPO_ROOT=${CMAKE_SOURCE_DIR}
            -P ${CMAKE_CURRENT_SOURCE_DIR}/toolchain/verify_clang_bootstrap_preset.cmake
    )
endif()

add_test(NAME clang_bootstrap_core_builds
    COMMAND ${CMAKE_COMMAND}
        --build ${CMAKE_BINARY_DIR}
        --target telemetry_core
)

add_executable(python_to_cpp_roundtrip_test
    ${CMAKE_CURRENT_SOURCE_DIR}/unit/proto/python_to_cpp_roundtrip_test.cpp
)

target_link_libraries(python_to_cpp_roundtrip_test
    PRIVATE
        telemetry::protos
)

telemetry_enable_warnings(python_to_cpp_roundtrip_test)
telemetry_enable_instrumentation(python_to_cpp_roundtrip_test)
add_dependencies(telemetry_tests python_to_cpp_roundtrip_test)

add_executable(telemetry_data_smoke_test
    ${CMAKE_CURRENT_SOURCE_DIR}/unit/core/telemetry_data_smoke_test.cpp
)

target_link_libraries(telemetry_data_smoke_test
    PRIVATE
        telemetry::core
)

telemetry_enable_warnings(telemetry_data_smoke_test)
telemetry_enable_instrumentation(telemetry_data_smoke_test)
add_dependencies(telemetry_tests telemetry_data_smoke_test)

add_test(NAME telemetry_data_smoke_test COMMAND $<TARGET_FILE:telemetry_data_smoke_test>)

add_test(
    NAME python_to_cpp_roundtrip_test
    COMMAND ${Python3_EXECUTABLE}
        ${CMAKE_SOURCE_DIR}/simulator-python/serialize_python_telemetry.py
        ${CMAKE_BINARY_DIR}/python_roundtrip_payload.bin
)
# Treat the Python payload as a fixture so parallel CTest runs cannot start the
# C++ consumer until serialization has completed successfully.
set_tests_properties(python_to_cpp_roundtrip_test PROPERTIES
    ENVIRONMENT "PYTHONPATH=${PROTO_PY_GENERATED_DIR}"
    FIXTURES_REQUIRED telemetry_test_binaries
    FIXTURES_SETUP python_telemetry_roundtrip_payload
)

add_test(
    NAME python_to_cpp_roundtrip_test_cpp
    COMMAND $<TARGET_FILE:python_to_cpp_roundtrip_test>
        ${CMAKE_BINARY_DIR}/python_roundtrip_payload.bin
)
set_tests_properties(python_to_cpp_roundtrip_test_cpp PROPERTIES
    FIXTURES_REQUIRED "telemetry_test_binaries;python_telemetry_roundtrip_payload"
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

        # This cross-language test is registered above because it requires a
        # Python-generated payload argument and explicit fixture ordering.
        if(relative_source STREQUAL "unit/proto/python_to_cpp_roundtrip_test.cpp")
            continue()
        endif()

        get_filename_component(test_name "${test_source}" NAME_WE)
        string(REPLACE "/" "_" test_target "${relative_source}")
        string(REPLACE "\\" "_" test_target "${test_target}")
        string(REPLACE "." "_" test_target "${test_target}")

        add_executable(${test_target} "${test_source}")
        target_link_libraries(${test_target}
            PRIVATE
                telemetry::core
        )

        if(relative_source MATCHES "^unit/proto/")
            target_link_libraries(${test_target}
                PRIVATE
                    telemetry::protos
            )
        endif()

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

        telemetry_enable_warnings(${test_target})
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

add_test(
    NAME unit_proto_python_contract_smoke
    COMMAND ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/unit/proto/test_proto_contract_smoke.py
)
set_tests_properties(unit_proto_python_contract_smoke PROPERTIES
    ENVIRONMENT "PYTHONPATH=${PROTO_PY_GENERATED_DIR}"
    FIXTURES_REQUIRED telemetry_test_binaries
)

add_test(
    NAME unit_simulator_python_tests
    COMMAND ${Python3_EXECUTABLE} -m unittest discover
        -s ${CMAKE_CURRENT_SOURCE_DIR}/unit/simulator
        -p "test_*.py"
        -v
)
# Use CMake's host-aware path-list operation so discovery works on Windows and Linux.
set_tests_properties(unit_simulator_python_tests PROPERTIES
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
    ENVIRONMENT_MODIFICATION
        "PYTHONPATH=path_list_prepend:${PROTO_PY_GENERATED_DIR};PYTHONPATH=path_list_prepend:${CMAKE_SOURCE_DIR}/simulator-python"
    FIXTURES_REQUIRED telemetry_test_binaries
)

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
    telemetry_enable_warnings(telemetry_placeholder_fuzzer)
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
    telemetry_enable_warnings(telemetry_benchmarks)
    telemetry_enable_instrumentation(telemetry_benchmarks)
endif()