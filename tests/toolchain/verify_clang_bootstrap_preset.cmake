cmake_minimum_required(VERSION 3.25)

if(NOT DEFINED REPO_ROOT)
    message(FATAL_ERROR "REPO_ROOT is required")
endif()

file(READ "${REPO_ROOT}/CMakePresets.json" presets_json)

foreach(required_entry IN ITEMS
    "\"name\": \"clang-base\""
    "\"name\": \"clang-bootstrap\""
    "\"CMAKE_CXX_COMPILER\": \"clang-cl\""
    "\"VCPKG_TARGET_TRIPLET\": \"x64-windows\""
)
    string(FIND "${presets_json}" "${required_entry}" required_index)
    if(required_index EQUAL -1)
        message(FATAL_ERROR "Missing expected preset entry: ${required_entry}")
    endif()
endforeach()

string(FIND "${presets_json}" "\"name\": \"debug\"" debug_index)
if(NOT debug_index EQUAL -1)
    message(FATAL_ERROR "Legacy debug preset is still present")
endif()

execute_process(
    COMMAND "${CMAKE_COMMAND}"
        -S "${REPO_ROOT}"
        -B "${REPO_ROOT}/build/clang-bootstrap-verify"
        -G Ninja
        -DCMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake
        -DCMAKE_CXX_COMPILER=clang-cl
        -DVCPKG_TARGET_TRIPLET=x64-windows
        -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
        -DBUILD_TESTING=ON
    RESULT_VARIABLE configure_result
    OUTPUT_VARIABLE configure_stdout
    ERROR_VARIABLE configure_stderr
)

if(NOT configure_result EQUAL 0)
    message(FATAL_ERROR
        "Clang bootstrap preset configure failed\nstdout:\n${configure_stdout}\nstderr:\n${configure_stderr}"
    )
endif()