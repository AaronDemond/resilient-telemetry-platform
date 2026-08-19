add_library(postgres_adapter STATIC 
        postgres_adapter.cpp
)


add_library(telemetry::postgres_adapter ALIAS postgres_adapter)

target_link_libraries(postgres_adapter
    PUBLIC
        telemetry::core
)

target_include_directories(postgres_adapter
    PUBLIC
    ${CMAKE_SOURCE_DIR}/cpp/include
)