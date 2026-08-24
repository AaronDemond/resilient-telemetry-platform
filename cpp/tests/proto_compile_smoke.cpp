#include <cstdint>

#include "envelope.pb.h"
#include "operator_request.pb.h"
#include "request_acknowledgement.pb.h"
#include "standard_error.pb.h"
#include "telemetry_event.pb.h"

int main() {
  telemetry::v1::Envelope envelope;
  envelope.set_message_id("msg-1");
  envelope.set_run_id("run-1");
  envelope.set_unit_id("unit-1");
  envelope.set_boot_id("boot-1");
  envelope.set_sequence_number(1);
  envelope.set_source_timestamp_ms(1700000000000LL);
  envelope.set_schema_version(1);

  telemetry::v1::TelemetryEvent event;
  event.set_unit_id("unit-1");
  event.set_boot_id("boot-1");
  event.set_schema_version(1);
  event.set_software_version("1.0.0");
  event.set_sequence_number(1);
  event.set_source_timestamp_ms(1700000000000LL);
  event.set_latitude(40.7128);
  event.set_longitude(-74.0060);
  event.set_fuel_remaining(88.5f);
  event.set_equipment_temperature_c(62.0f);
  event.set_connectivity_quality(0.91f);
  event.mutable_health_flags()->set_temperature_warning(false);
  event.mutable_health_flags()->set_connectivity_degraded(false);
  event.mutable_health_flags()->set_maintenance_required(false);
  event.set_status(telemetry::v1::UNIT_STATUS_AVAILABLE);
  event.set_correlation_id("corr-1");

  telemetry::v1::OperatorRequest request;
  auto* req = request.mutable_change_sampling_interval();
  req->set_interval_ms(5000);

  telemetry::v1::RequestAcknowledgement ack;
  ack.set_request_id("req-1");
  ack.set_unit_id("unit-1");
  ack.set_boot_id("boot-1");
  ack.set_correlation_id("corr-1");
  ack.set_status(telemetry::v1::ACK_STATUS_APPLIED);

  telemetry::v1::StandardError err;
  err.set_code(telemetry::v1::ERROR_CODE_VALIDATION_FAILED);
  err.set_message("validation failed");
  err.set_source_field("sequence_number");
  (*err.mutable_metadata())["rule"] = "monotonic";

  return envelope.ByteSizeLong() > 0 && event.ByteSizeLong() > 0 && request.ByteSizeLong() > 0 &&
         ack.ByteSizeLong() > 0 && err.ByteSizeLong() > 0 ? 0 : 1;
}
