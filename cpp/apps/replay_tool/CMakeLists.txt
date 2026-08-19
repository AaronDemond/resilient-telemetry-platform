# cpp/apps/replay-tool/CMakeLists.txt
add_executable(replay_tool main.cpp)
add_executable(telemetry::replay_tool ALIAS replay_tool)

target_link_libraries(replay_tool
    PRIVATE
        telemetry::core
        telemetry::postgres_adapter
)