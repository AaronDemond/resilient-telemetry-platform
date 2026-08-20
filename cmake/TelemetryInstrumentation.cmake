add_library(telemetry_instrumentation INTERFACE)

include(CheckCXXCompilerFlag)

function(telemetry_require_compiler_flag compiler_flag)
    string(MAKE_C_IDENTIFIER "${compiler_flag}" compiler_flag_identifier)
    set(compiler_flag_check "telemetry_supports_${compiler_flag_identifier}")
    check_cxx_compiler_flag("${compiler_flag}" ${compiler_flag_check})

    if(NOT ${compiler_flag_check})
        message(FATAL_ERROR
            "${CMAKE_CXX_COMPILER_ID} does not support the required instrumentation flag ${compiler_flag}")
    endif()
endfunction()

if(CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
    if(TELEMETRY_ENABLE_ASAN)
        telemetry_require_compiler_flag("-fsanitize=address")
        target_compile_options(telemetry_instrumentation INTERFACE
            -fsanitize=address
            -fno-omit-frame-pointer)
        target_link_options(telemetry_instrumentation INTERFACE
            -fsanitize=address)
    endif()

    if(TELEMETRY_ENABLE_UBSAN)
        telemetry_require_compiler_flag("-fsanitize=undefined")
        target_compile_options(telemetry_instrumentation INTERFACE
            -fsanitize=undefined
            -fno-omit-frame-pointer)
        target_link_options(telemetry_instrumentation INTERFACE
            -fsanitize=undefined)
    endif()

    if(TELEMETRY_ENABLE_TSAN)
        telemetry_require_compiler_flag("-fsanitize=thread")
        target_compile_options(telemetry_instrumentation INTERFACE
            -fsanitize=thread
            -fno-omit-frame-pointer)
        target_link_options(telemetry_instrumentation INTERFACE
            -fsanitize=thread)
    endif()

    if(TELEMETRY_ENABLE_COVERAGE)
        telemetry_require_compiler_flag("--coverage")
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