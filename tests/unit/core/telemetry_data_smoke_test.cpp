#include <cassert>
#include <iostream>
#include <string>

#include "telemetry/core/telemetry_data.hpp"

int main() {
    telemetry::v1::TelemetryMessage proto_message;
    auto* envelope = proto_message.mutable_envelope();
    envelope->set_message_id("msg-001");
    envelope->set_run_id("run-001");
    envelope->set_unit_id("unit-42");
    envelope->set_boot_id("boot-7");
    envelope->set_session_id("session-7");
    envelope->set_sequence_number(17);
    envelope->set_source_timestamp_ms(1700000000000LL);
    envelope->set_schema_version(1);
    envelope->set_correlation_id("corr-abc-1");

    auto* event = proto_message.mutable_event();
    event->set_unit_id("unit-42");
    event->set_boot_id("boot-7");
    event->set_schema_version(1);
    event->set_software_version("1.0.0");
    event->set_sequence_number(17);
    event->set_source_timestamp_ms(1700000000000LL);
    event->set_latitude(40.7128);
    event->set_longitude(-74.0060);
    event->set_fuel_remaining(88.5F);
    event->set_equipment_temperature_c(62.0F);
    event->set_connectivity_quality(0.91F);
    auto* flags = event->mutable_health_flags();
    flags->set_temperature_warning(false);
    flags->set_connectivity_degraded(false);
    flags->set_maintenance_required(false);
    event->set_status(telemetry::v1::UNIT_STATUS_AVAILABLE);
    event->set_correlation_id("corr-abc-1");

    telemetry::core::TelemetryData original{proto_message};
    const std::string payload = original.serialize();
    const auto round_tripped = telemetry::core::TelemetryData::deserialize(payload);

    if (!round_tripped.message().has_envelope()) {
        std::cerr << "Round-trip deserialization missing envelope\n";
        return 1;
    }

    if (!round_tripped.message().has_event()) {
        std::cerr << "Round-trip deserialization missing event\n";
        return 1;
    }

    if (round_tripped.message().SerializeAsString() != payload) {
        std::cerr << "Round-trip payload mismatch\n";
        return 1;
    }

    telemetry::core::TelemetryData mutated;
    mutated.set_message_id("msg-002");
    mutated.set_run_id("run-002");
    mutated.set_unit_id("unit-99");
    mutated.set_boot_id("boot-88");
    mutated.set_session_id("session-88");
    mutated.set_sequence_number(99);
    mutated.set_source_timestamp_ms(1800000000000LL);
    mutated.set_schema_version(2);
    mutated.set_correlation_id("corr-xyz-2");
    mutated.set_software_version("2.4.1");
    mutated.set_latitude(51.5074);
    mutated.set_longitude(-0.1278);
    mutated.set_fuel_remaining(42.25F);
    mutated.set_equipment_temperature_c(71.5F);
    mutated.set_connectivity_quality(0.76F);
    mutated.set_temperature_warning(true);
    mutated.set_connectivity_degraded(true);
    mutated.set_maintenance_required(true);
    mutated.set_status(telemetry::v1::UNIT_STATUS_EN_ROUTE);

    if (mutated.message().envelope().message_id() != "msg-002") {
        std::cerr << "Envelope message_id mismatch after setter update\n";
        return 1;
    }

    if (mutated.message().event().unit_id() != "unit-99") {
        std::cerr << "Event unit_id mismatch after setter update\n";
        return 1;
    }

    if (mutated.message().event().health_flags().temperature_warning() != true ||
        mutated.message().event().health_flags().connectivity_degraded() != true ||
        mutated.message().event().health_flags().maintenance_required() != true) {
        std::cerr << "Health flag mismatch after setter update\n";
        return 1;
    }

    const auto proto = mutated.to_proto();
    const auto reconstructed = telemetry::core::TelemetryData::from_proto(proto);

    if (reconstructed.message().envelope().correlation_id() != "corr-xyz-2") {
        std::cerr << "From_proto correlation_id mismatch\n";
        return 1;
    }

    if (reconstructed.message().event().status() != telemetry::v1::UNIT_STATUS_EN_ROUTE) {
        std::cerr << "From_proto status mismatch\n";
        return 1;
    }

    std::cout << "TelemetryData round-trip OK\n";
    return 0;
}
