#include <cmath>
#include <iostream>
#include <string>

#include "envelope.pb.h"
#include "operator_request.pb.h"
#include "request_acknowledgement.pb.h"
#include "standard_error.pb.h"
#include "telemetry_event.pb.h"

namespace {

bool CheckEnvelopeContract(const telemetry::v1::Envelope& envelope) {
  if (envelope.message_id().empty()) return false;
  if (envelope.run_id().empty()) return false;
  if (envelope.unit_id().empty()) return false;
  if (envelope.boot_id().empty()) return false;
  if (envelope.sequence_number() < 1u) return false;
  if (envelope.source_timestamp_ms() < 0) return false;
  if (envelope.schema_version() < 1u) return false;
  return true;
}

bool CheckTelemetryEventContract(const telemetry::v1::TelemetryEvent& event) {
  if (event.unit_id().empty()) return false;
  if (event.boot_id().empty()) return false;
  if (event.schema_version() < 1u) return false;
  if (event.software_version().empty()) return false;
  if (event.sequence_number() < 1u) return false;
  if (event.source_timestamp_ms() < 0) return false;
  if (event.fuel_remaining() < 0.0f || event.fuel_remaining() > 100.0f) return false;
  if (event.equipment_temperature_c() < -50.0f || event.equipment_temperature_c() > 120.0f) return false;
  if (event.connectivity_quality() < 0.0f || event.connectivity_quality() > 1.0f) return false;
  if (event.status() == telemetry::v1::UNIT_STATUS_UNSPECIFIED) return false;
  return true;
}

bool Require(bool condition, const std::string& message) {
  if (!condition) {
    std::cerr << "PROTO SMOKE FAIL: " << message << '\n';
    return false;
  }
  return true;
}

}  // namespace

int main() {
  telemetry::v1::Envelope envelope;
  envelope.set_message_id("msg-001");
  envelope.set_run_id("run-001");
  envelope.set_unit_id("unit-42");
  envelope.set_boot_id("boot-7");
  envelope.set_session_id("session-7");
  envelope.set_sequence_number(17);
  envelope.set_source_timestamp_ms(1700000000000LL);
  envelope.set_schema_version(1);
  envelope.set_correlation_id("corr-abc-1");

  if (!Require(CheckEnvelopeContract(envelope), "Envelope contract check failed before serialization")) {
    return 1;
  }

  const std::string envelope_payload = envelope.SerializeAsString();
  if (!Require(!envelope_payload.empty(), "Envelope serialization produced empty payload")) {
    return 1;
  }

  telemetry::v1::Envelope envelope_decoded;
  if (!Require(envelope_decoded.ParseFromString(envelope_payload), "Envelope parse failed")) {
    return 1;
  }
  if (!Require(envelope_decoded.message_id() == envelope.message_id(), "Envelope message_id mismatch")) {
    return 1;
  }
  if (!Require(envelope_decoded.run_id() == envelope.run_id(), "Envelope run_id mismatch")) {
    return 1;
  }
  if (!Require(envelope_decoded.unit_id() == envelope.unit_id(), "Envelope unit_id mismatch")) {
    return 1;
  }
  if (!Require(envelope_decoded.boot_id() == envelope.boot_id(), "Envelope boot_id mismatch")) {
    return 1;
  }
  if (!Require(CheckEnvelopeContract(envelope_decoded), "Envelope contract check failed after deserialization")) {
    return 1;
  }

  telemetry::v1::TelemetryEvent event;
  event.set_unit_id("unit-42");
  event.set_boot_id("boot-7");
  event.set_schema_version(1);
  event.set_software_version("1.0.0");
  event.set_sequence_number(17);
  event.set_source_timestamp_ms(1700000000000LL);
  event.set_latitude(40.7128);
  event.set_longitude(-74.0060);
  event.set_fuel_remaining(88.5f);
  event.set_equipment_temperature_c(62.0f);
  event.set_connectivity_quality(0.91f);
  auto* flags = event.mutable_health_flags();
  flags->set_temperature_warning(false);
  flags->set_connectivity_degraded(false);
  flags->set_maintenance_required(false);
  event.set_status(telemetry::v1::UNIT_STATUS_AVAILABLE);
  event.set_correlation_id("corr-abc-1");

  if (!Require(CheckTelemetryEventContract(event), "TelemetryEvent contract check failed before serialization")) {
    return 1;
  }
  if (!Require(std::fabs(event.latitude() - 40.7128) < 1e-12, "TelemetryEvent latitude type/range invalid")) {
    return 1;
  }
  if (!Require(std::fabs(event.longitude() + 74.0060) < 1e-12, "TelemetryEvent longitude type/range invalid")) {
    return 1;
  }

  const std::string event_payload = event.SerializeAsString();
  if (!Require(!event_payload.empty(), "TelemetryEvent serialization produced empty payload")) {
    return 1;
  }

  telemetry::v1::TelemetryEvent event_decoded;
  if (!Require(event_decoded.ParseFromString(event_payload), "TelemetryEvent parse failed")) {
    return 1;
  }
  if (!Require(std::fabs(event_decoded.latitude() - event.latitude()) < 1e-12, "TelemetryEvent latitude mismatch")) {
    return 1;
  }
  if (!Require(std::fabs(event_decoded.longitude() - event.longitude()) < 1e-12, "TelemetryEvent longitude mismatch")) {
    return 1;
  }
  if (!Require(CheckTelemetryEventContract(event_decoded), "TelemetryEvent contract check failed after deserialization")) {
    return 1;
  }

  telemetry::v1::OperatorRequest request;
  request.set_request_id("req-42");
  request.set_unit_id("unit-42");
  request.set_boot_id("boot-7");
  request.set_correlation_id("corr-abc-1");
  auto* interval = request.mutable_change_sampling_interval();
  interval->set_interval_ms(5000);

  if (!Require(request.has_change_sampling_interval(), "OperatorRequest change_sampling_interval missing")) {
    return 1;
  }
  if (!Require(request.change_sampling_interval().interval_ms() == 5000u, "OperatorRequest interval value invalid")) {
    return 1;
  }

  const std::string request_payload = request.SerializeAsString();
  if (!Require(!request_payload.empty(), "OperatorRequest serialization produced empty payload")) {
    return 1;
  }

  telemetry::v1::OperatorRequest request_decoded;
  if (!Require(request_decoded.ParseFromString(request_payload), "OperatorRequest parse failed")) {
    return 1;
  }
  if (!Require(request_decoded.has_change_sampling_interval(), "OperatorRequest oneof not preserved")) {
    return 1;
  }

  telemetry::v1::RequestAcknowledgement ack;
  ack.set_request_id("req-42");
  ack.set_unit_id("unit-42");
  ack.set_boot_id("boot-7");
  ack.set_correlation_id("corr-abc-1");
  ack.set_status(telemetry::v1::ACK_STATUS_APPLIED);
  auto* ack_response = ack.mutable_change_sampling_interval();
  ack_response->set_applied_interval_ms(5000);

  if (!Require(ack.has_change_sampling_interval(), "RequestAcknowledgement change_sampling_interval missing")) {
    return 1;
  }
  if (!Require(ack.status() == telemetry::v1::ACK_STATUS_APPLIED, "RequestAcknowledgement status invalid")) {
    return 1;
  }

  const std::string ack_payload = ack.SerializeAsString();
  if (!Require(!ack_payload.empty(), "RequestAcknowledgement serialization produced empty payload")) {
    return 1;
  }

  telemetry::v1::RequestAcknowledgement ack_decoded;
  if (!Require(ack_decoded.ParseFromString(ack_payload), "RequestAcknowledgement parse failed")) {
    return 1;
  }
  if (!Require(ack_decoded.has_change_sampling_interval(), "RequestAcknowledgement oneof not preserved")) {
    return 1;
  }

  telemetry::v1::StandardError error;
  error.set_code(telemetry::v1::ERROR_CODE_VALIDATION_FAILED);
  error.set_message("validation failed");
  error.set_source_field("sequence_number");
  (*error.mutable_metadata())["rule"] = "monotonic";

  if (!Require(error.code() == telemetry::v1::ERROR_CODE_VALIDATION_FAILED, "StandardError code invalid")) {
    return 1;
  }
  if (!Require(!error.message().empty(), "StandardError message missing")) {
    return 1;
  }
  if (!Require(!error.source_field().empty(), "StandardError source_field missing")) {
    return 1;
  }
  if (!Require(error.metadata().contains("rule"), "StandardError metadata missing rule")) {
    return 1;
  }

  const std::string error_payload = error.SerializeAsString();
  if (!Require(!error_payload.empty(), "StandardError serialization produced empty payload")) {
    return 1;
  }

  telemetry::v1::StandardError error_decoded;
  if (!Require(error_decoded.ParseFromString(error_payload), "StandardError parse failed")) {
    return 1;
  }
  if (!Require(error_decoded.metadata().at("rule") == "monotonic", "StandardError metadata mismatch")) {
    return 1;
  }

  return 0;
}
