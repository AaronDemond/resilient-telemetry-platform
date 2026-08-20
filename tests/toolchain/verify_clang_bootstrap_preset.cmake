cmake_minimum_required(VERSION 3.25)

if(NOT DEFINED REPO_ROOT)
    message(FATAL_ERROR "REPO_ROOT is required")
endif()

file(READ "${REPO_ROOT}/CMakePresets.json" presets_json)

foreach(required_entry IN ITEMS
    "\"name\": \"clang-base\""
    "\"name\": \"clang-bootstrap\""
    "\"CMAKE_CXX_COMPILER\": \"clang++\""
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

cmake_path(APPEND REPO_ROOT "build" "clang-bootstrap-verify" OUTPUT_VARIABLE verification_build_dir)

execute_process(
    COMMAND "${CMAKE_COMMAND}"
        --preset clang-bootstrap
        -B "${verification_build_dir}"
    WORKING_DIRECTORY "${REPO_ROOT}"
    RESULT_VARIABLE configure_result
    OUTPUT_VARIABLE configure_stdout
    ERROR_VARIABLE configure_stderr
)

if(NOT configure_result EQUAL 0)
    message(FATAL_ERROR
        "Clang bootstrap preset configure failed\nstdout:\n${configure_stdout}\nstderr:\n${configure_stderr}"
    )
endif()