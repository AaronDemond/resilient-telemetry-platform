add_library(telemetry_instrumentation INTERFACE)

include(CheckCXXSourceCompiles)
include(CMakePushCheckState)

option(TELEMETRY_WARNINGS_AS_ERRORS
    "Treat project compiler warnings as errors"
    OFF)

function(telemetry_require_compiler_flag compiler_flag)
    string(MAKE_C_IDENTIFIER "${compiler_flag}" compiler_flag_identifier)
    set(compiler_flag_check "telemetry_can_use_${compiler_flag_identifier}")

    cmake_push_check_state(RESET)
    set(CMAKE_REQUIRED_FLAGS "${compiler_flag}")
    set(CMAKE_REQUIRED_LINK_OPTIONS "${compiler_flag}")
    check_cxx_source_compiles("int main() { return 0; }" ${compiler_flag_check})
    cmake_pop_check_state()

    if(NOT ${compiler_flag_check})
        message(FATAL_ERROR
            "${CMAKE_CXX_COMPILER_ID} cannot compile and link with the required instrumentation flag ${compiler_flag}")
    endif()
endfunction()

function(telemetry_enable_warnings target_name)
    target_compile_options(${target_name} PRIVATE
        -Wall
        -Wextra
        -Wpedantic
        -Wconversion
        -Wsign-conversion
        -Wshadow
        -Wformat=2
        -Wundef
        -Wnon-virtual-dtor
        -Wold-style-cast
        -Woverloaded-virtual)

    if(TELEMETRY_WARNINGS_AS_ERRORS)
        target_compile_options(${target_name} PRIVATE -Werror)
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