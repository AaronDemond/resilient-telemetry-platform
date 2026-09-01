# cpp/src/adapters/nats/CMakeLists.txt
add_library(nats_adapter STATIC
    nats_adapter.cpp
)

add_library(telemetry::nats_adapter ALIAS nats_adapter)

# cnats exports link requirements on OpenSSL and Threads. Import those first,
# otherwise the package config fails while evaluating the imported target.
find_package(OpenSSL REQUIRED)
find_package(Threads REQUIRED)
find_package(cnats CONFIG REQUIRED)

# vcpkg exports either the shared or static target depending on the selected triplet.
if(TARGET cnats::nats)
    set(_telemetry_cnats_target cnats::nats)
elseif(TARGET cnats::nats_static)
    set(_telemetry_cnats_target cnats::nats_static)
else()
    message(FATAL_ERROR
        "cnats target not found. Expected cnats::nats or cnats::nats_static for the active vcpkg triplet."
    )
endif()

target_link_libraries(nats_adapter
    PUBLIC
        telemetry::core
        ${_telemetry_cnats_target}
)

target_include_directories(nats_adapter
    PUBLIC
        ${CMAKE_SOURCE_DIR}/cpp/include
)

telemetry_enable_warnings(nats_adapter)
telemetry_enable_instrumentation(nats_adapter)