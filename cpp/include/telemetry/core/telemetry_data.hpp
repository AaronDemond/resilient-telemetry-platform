#pragma once

#include <cstdint>
#include <string>

#include "telemetry/v1/telemetry_message.pb.h"

namespace telemetry::core {

// Thin wrapper around the generated protobuf message used as the canonical contract.
// The wrapper keeps a single message state while exposing ergonomic accessors for app code.
class TelemetryData {
public:
    TelemetryData() = default;
    // Copies lvalue messages and moves rvalue messages into the wrapper.
    explicit TelemetryData(telemetry::v1::TelemetryMessage message);

    [[nodiscard]] const telemetry::v1::TelemetryMessage& message() const noexcept;
    [[nodiscard]] telemetry::v1::TelemetryMessage& mutable_message() noexcept;

    [[nodiscard]] bool has_envelope() const noexcept;
    [[nodiscard]] bool has_event() const noexcept;

    [[nodiscard]] const std::string& message_id() const noexcept;
    [[nodiscard]] const std::string& run_id() const noexcept;
    [[nodiscard]] const std::string& unit_id() const noexcept;
    [[nodiscard]] const std::string& boot_id() const noexcept;
    [[nodiscard]] const std::string& session_id() const noexcept;
    [[nodiscard]] std::uint64_t sequence_number() const noexcept;
    [[nodiscard]] std::int64_t source_timestamp_ms() const noexcept;
    [[nodiscard]] std::uint32_t schema_version() const noexcept;
    [[nodiscard]] const std::string& correlation_id() const noexcept;
    [[nodiscard]] const std::string& software_version() const noexcept;
    [[nodiscard]] double latitude() const noexcept;
    [[nodiscard]] double longitude() const noexcept;
    [[nodiscard]] float fuel_remaining() const noexcept;
    [[nodiscard]] float equipment_temperature_c() const noexcept;
    [[nodiscard]] float connectivity_quality() const noexcept;
    [[nodiscard]] bool temperature_warning() const noexcept;
    [[nodiscard]] bool connectivity_degraded() const noexcept;
    [[nodiscard]] bool maintenance_required() const noexcept;
    [[nodiscard]] telemetry::v1::UnitStatus status() const noexcept;

    void set_message_id(std::string value);
    void set_run_id(std::string value);
    void set_unit_id(std::string value);
    void set_boot_id(std::string value);
    void set_session_id(std::string value);
    void set_sequence_number(std::uint64_t value);
    void set_source_timestamp_ms(std::int64_t value);
    void set_schema_version(std::uint32_t value);
    void set_correlation_id(std::string value);
    void set_software_version(std::string value);
    void set_latitude(double value);
    void set_longitude(double value);
    void set_fuel_remaining(float value);
    void set_equipment_temperature_c(float value);
    void set_connectivity_quality(float value);
    void set_temperature_warning(bool value);
    void set_connectivity_degraded(bool value);
    void set_maintenance_required(bool value);
    void set_status(telemetry::v1::UnitStatus value);

    [[nodiscard]] telemetry::v1::TelemetryMessage to_proto() const;
    [[nodiscard]] static TelemetryData from_proto(const telemetry::v1::TelemetryMessage& message);

    [[nodiscard]] std::string serialize() const;
    [[nodiscard]] static TelemetryData deserialize(const std::string& payload);

private:
    telemetry::v1::TelemetryMessage message_;
};

}  // namespace telemetry::core
