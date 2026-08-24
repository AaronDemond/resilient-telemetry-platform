#include "telemetry/core/telemetry_data.hpp"

#include <stdexcept>
#include <utility>

namespace telemetry::core {

// Note: the protobuf object remains the source of truth for the wire format and field layout.
// This wrapper only forwards state and convenience methods without duplicating the schema.
TelemetryData::TelemetryData(telemetry::v1::TelemetryMessage message)
    : message_(std::move(message)) {}

TelemetryData::TelemetryData(const telemetry::v1::TelemetryMessage& message)
    : message_(message) {}

const telemetry::v1::TelemetryMessage& TelemetryData::message() const noexcept {
    return message_;
}

telemetry::v1::TelemetryMessage& TelemetryData::mutable_message() noexcept {
    return message_;
}

bool TelemetryData::has_envelope() const noexcept {
    return message_.has_envelope();
}

bool TelemetryData::has_event() const noexcept {
    return message_.has_event();
}

const std::string& TelemetryData::message_id() const noexcept {
    return message_.envelope().message_id();
}

const std::string& TelemetryData::run_id() const noexcept {
    return message_.envelope().run_id();
}

const std::string& TelemetryData::unit_id() const noexcept {
    return message_.envelope().unit_id();
}

const std::string& TelemetryData::boot_id() const noexcept {
    return message_.envelope().boot_id();
}

const std::string& TelemetryData::session_id() const noexcept {
    return message_.envelope().session_id();
}

std::uint64_t TelemetryData::sequence_number() const noexcept {
    return message_.envelope().sequence_number();
}

std::int64_t TelemetryData::source_timestamp_ms() const noexcept {
    return message_.envelope().source_timestamp_ms();
}

std::uint32_t TelemetryData::schema_version() const noexcept {
    return message_.envelope().schema_version();
}

const std::string& TelemetryData::correlation_id() const noexcept {
    return message_.envelope().correlation_id();
}

const std::string& TelemetryData::software_version() const noexcept {
    return message_.event().software_version();
}

double TelemetryData::latitude() const noexcept {
    return message_.event().latitude();
}

double TelemetryData::longitude() const noexcept {
    return message_.event().longitude();
}

float TelemetryData::fuel_remaining() const noexcept {
    return message_.event().fuel_remaining();
}

float TelemetryData::equipment_temperature_c() const noexcept {
    return message_.event().equipment_temperature_c();
}

float TelemetryData::connectivity_quality() const noexcept {
    return message_.event().connectivity_quality();
}

bool TelemetryData::temperature_warning() const noexcept {
    return message_.event().health_flags().temperature_warning();
}

bool TelemetryData::connectivity_degraded() const noexcept {
    return message_.event().health_flags().connectivity_degraded();
}

bool TelemetryData::maintenance_required() const noexcept {
    return message_.event().health_flags().maintenance_required();
}

telemetry::v1::UnitStatus TelemetryData::status() const noexcept {
    return message_.event().status();
}

void TelemetryData::set_message_id(std::string value) {
    message_.mutable_envelope()->set_message_id(std::move(value));
}

void TelemetryData::set_run_id(std::string value) {
    message_.mutable_envelope()->set_run_id(std::move(value));
}

void TelemetryData::set_unit_id(std::string value) {
    message_.mutable_envelope()->set_unit_id(value);
    message_.mutable_event()->set_unit_id(std::move(value));
}

void TelemetryData::set_boot_id(std::string value) {
    message_.mutable_envelope()->set_boot_id(value);
    message_.mutable_event()->set_boot_id(std::move(value));
}

void TelemetryData::set_session_id(std::string value) {
    message_.mutable_envelope()->set_session_id(std::move(value));
}

void TelemetryData::set_sequence_number(std::uint64_t value) {
    message_.mutable_envelope()->set_sequence_number(value);
    message_.mutable_event()->set_sequence_number(value);
}

void TelemetryData::set_source_timestamp_ms(std::int64_t value) {
    message_.mutable_envelope()->set_source_timestamp_ms(value);
    message_.mutable_event()->set_source_timestamp_ms(value);
}

void TelemetryData::set_schema_version(std::uint32_t value) {
    message_.mutable_envelope()->set_schema_version(value);
    message_.mutable_event()->set_schema_version(value);
}

void TelemetryData::set_correlation_id(std::string value) {
    message_.mutable_envelope()->set_correlation_id(value);
    message_.mutable_event()->set_correlation_id(std::move(value));
}

void TelemetryData::set_software_version(std::string value) {
    message_.mutable_event()->set_software_version(std::move(value));
}

void TelemetryData::set_latitude(double value) {
    message_.mutable_event()->set_latitude(value);
}

void TelemetryData::set_longitude(double value) {
    message_.mutable_event()->set_longitude(value);
}

void TelemetryData::set_fuel_remaining(float value) {
    message_.mutable_event()->set_fuel_remaining(value);
}

void TelemetryData::set_equipment_temperature_c(float value) {
    message_.mutable_event()->set_equipment_temperature_c(value);
}

void TelemetryData::set_connectivity_quality(float value) {
    message_.mutable_event()->set_connectivity_quality(value);
}

void TelemetryData::set_temperature_warning(bool value) {
    message_.mutable_event()->mutable_health_flags()->set_temperature_warning(value);
}

void TelemetryData::set_connectivity_degraded(bool value) {
    message_.mutable_event()->mutable_health_flags()->set_connectivity_degraded(value);
}

void TelemetryData::set_maintenance_required(bool value) {
    message_.mutable_event()->mutable_health_flags()->set_maintenance_required(value);
}

void TelemetryData::set_status(telemetry::v1::UnitStatus value) {
    message_.mutable_event()->set_status(value);
}

telemetry::v1::TelemetryMessage TelemetryData::to_proto() const {
    return message_;
}

TelemetryData TelemetryData::from_proto(const telemetry::v1::TelemetryMessage& message) {
    return TelemetryData{message};
}

std::string TelemetryData::serialize() const {
    return message_.SerializeAsString();
}

TelemetryData TelemetryData::deserialize(const std::string& payload) {
    telemetry::v1::TelemetryMessage message;
    if (!message.ParseFromString(payload)) {
        throw std::invalid_argument("Failed to deserialize TelemetryData payload");
    }
    return TelemetryData{message};
}

}  // namespace telemetry::core
