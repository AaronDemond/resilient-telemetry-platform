add_library(telemetry_instrumentation INTERFACE)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    if(TELEMETRY_ENABLE_ASAN)
        target_compile_options(telemetry_instrumentation INTERFACE
            -fsanitize=address
            -fno-omit-frame-pointer)
        target_link_options(telemetry_instrumentation INTERFACE
            -fsanitize=address)
    endif()

    if(TELEMETRY_ENABLE_UBSAN)
        target_compile_options(telemetry_instrumentation INTERFACE
            -fsanitize=undefined
            -fno-omit-frame-pointer)
        target_link_options(telemetry_instrumentation INTERFACE
            -fsanitize=undefined)
    endif()

    if(TELEMETRY_ENABLE_TSAN)
        target_compile_options(telemetry_instrumentation INTERFACE
            -fsanitize=thread
            -fno-omit-frame-pointer)
        target_link_options(telemetry_instrumentation INTERFACE
            -fsanitize=thread)
    endif()

    if(TELEMETRY_ENABLE_COVERAGE)
        target_compile_options(telemetry_instrumentation INTERFACE
            --coverage -O0 -g)
        target_link_options(telemetry_instrumentation INTERFACE
            --coverage)
    endif()
endif()

function(telemetry_enable_instrumentation target_name)
    target_link_libraries(${target_name}
        PRIVATE telemetry_instrumentation)
endfunction()