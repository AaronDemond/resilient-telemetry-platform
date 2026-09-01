#pragma once

#include <string_view>

namespace pqxx {
class connection;
}

namespace telemetry::core {
class TelemetryData;
}

namespace telemetry::adapters::postgres {

[[nodiscard]] const char* adapter_name() noexcept;

void ensure_telemetry_schema(pqxx::connection& connection);

void store_telemetry_message(
    pqxx::connection& connection,
    const telemetry::core::TelemetryData& telemetry,
    std::string_view raw_payload);

}  // namespace telemetry::adapters::postgres