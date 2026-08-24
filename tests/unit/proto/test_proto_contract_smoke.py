import unittest

from telemetry.v1 import (
    envelope_pb2,
    operator_request_pb2,
    request_acknowledgement_pb2,
    standard_error_pb2,
    telemetry_event_pb2,
)


class GeneratedProtoContractSmokeTest(unittest.TestCase):
    def _assert_required_envelope_fields(self, envelope):
        self.assertTrue(envelope.message_id)
        self.assertTrue(envelope.run_id)
        self.assertTrue(envelope.unit_id)
        self.assertTrue(envelope.boot_id)
        self.assertGreaterEqual(envelope.sequence_number, 1)
        self.assertGreaterEqual(envelope.source_timestamp_ms, 0)
        self.assertGreaterEqual(envelope.schema_version, 1)

    def _assert_required_event_fields(self, event):
        self.assertTrue(event.unit_id)
        self.assertTrue(event.boot_id)
        self.assertGreaterEqual(event.schema_version, 1)
        self.assertTrue(event.software_version)
        self.assertGreaterEqual(event.sequence_number, 1)
        self.assertGreaterEqual(event.source_timestamp_ms, 0)
        self.assertGreaterEqual(event.fuel_remaining, 0.0)
        self.assertLessEqual(event.fuel_remaining, 100.0)
        self.assertGreaterEqual(event.equipment_temperature_c, -50.0)
        self.assertLessEqual(event.equipment_temperature_c, 120.0)
        self.assertGreaterEqual(event.connectivity_quality, 0.0)
        self.assertLessEqual(event.connectivity_quality, 1.0)
        self.assertIsInstance(event.health_flags, type(event.health_flags))
        self.assertIn(event.status, (
            telemetry_event_pb2.UNIT_STATUS_UNSPECIFIED,
            telemetry_event_pb2.UNIT_STATUS_AVAILABLE,
            telemetry_event_pb2.UNIT_STATUS_EN_ROUTE,
            telemetry_event_pb2.UNIT_STATUS_RETURNING,
        ))
        self.assertNotEqual(event.status, telemetry_event_pb2.UNIT_STATUS_UNSPECIFIED)

    def test_envelope_round_trip_and_contract(self):
        envelope = envelope_pb2.Envelope()
        envelope.message_id = "msg-001"
        envelope.run_id = "run-001"
        envelope.unit_id = "unit-42"
        envelope.boot_id = "boot-7"
        envelope.session_id = "session-7"
        envelope.sequence_number = 17
        envelope.source_timestamp_ms = 1700000000000
        envelope.schema_version = 1
        envelope.correlation_id = "corr-abc-1"

        self._assert_required_envelope_fields(envelope)

        payload = envelope.SerializeToString()
        self.assertGreater(len(payload), 0)

        decoded = envelope_pb2.Envelope()
        decoded.ParseFromString(payload)
        self.assertEqual(decoded, envelope)
        self._assert_required_envelope_fields(decoded)

    def test_telemetry_event_round_trip_and_contract(self):
        event = telemetry_event_pb2.TelemetryEvent()
        event.unit_id = "unit-42"
        event.boot_id = "boot-7"
        event.schema_version = 1
        event.software_version = "1.0.0"
        event.sequence_number = 17
        event.source_timestamp_ms = 1700000000000
        event.latitude = 40.7128
        event.longitude = -74.0060
        event.fuel_remaining = 88.5
        event.equipment_temperature_c = 62.0
        event.connectivity_quality = 0.91
        event.health_flags.temperature_warning = False
        event.health_flags.connectivity_degraded = False
        event.health_flags.maintenance_required = False
        event.status = telemetry_event_pb2.UNIT_STATUS_AVAILABLE
        event.correlation_id = "corr-abc-1"

        self._assert_required_event_fields(event)
        self.assertIsInstance(event.latitude, float)
        self.assertIsInstance(event.longitude, float)
        self.assertIsInstance(event.fuel_remaining, float)
        self.assertIsInstance(event.equipment_temperature_c, float)
        self.assertIsInstance(event.connectivity_quality, float)

        payload = event.SerializeToString()
        self.assertGreater(len(payload), 0)

        decoded = telemetry_event_pb2.TelemetryEvent()
        decoded.ParseFromString(payload)
        self.assertEqual(decoded, event)
        self._assert_required_event_fields(decoded)

    def test_operator_request_and_ack_round_trip_contract(self):
        request = operator_request_pb2.OperatorRequest()
        request.request_id = "req-42"
        request.unit_id = "unit-42"
        request.boot_id = "boot-7"
        request.correlation_id = "corr-abc-1"
        request.change_sampling_interval.interval_ms = 5000

        self.assertTrue(request.HasField("change_sampling_interval"))
        self.assertEqual(request.change_sampling_interval.interval_ms, 5000)

        payload = request.SerializeToString()
        self.assertGreater(len(payload), 0)

        decoded = operator_request_pb2.OperatorRequest()
        decoded.ParseFromString(payload)
        self.assertEqual(decoded, request)
        self.assertTrue(decoded.HasField("change_sampling_interval"))

        ack = request_acknowledgement_pb2.RequestAcknowledgement()
        ack.request_id = "req-42"
        ack.unit_id = "unit-42"
        ack.boot_id = "boot-7"
        ack.correlation_id = "corr-abc-1"
        ack.status = request_acknowledgement_pb2.ACK_STATUS_APPLIED
        ack.change_sampling_interval.applied_interval_ms = 5000

        self.assertTrue(ack.HasField("change_sampling_interval"))
        self.assertEqual(ack.status, request_acknowledgement_pb2.ACK_STATUS_APPLIED)

        ack_payload = ack.SerializeToString()
        self.assertGreater(len(ack_payload), 0)

        decoded_ack = request_acknowledgement_pb2.RequestAcknowledgement()
        decoded_ack.ParseFromString(ack_payload)
        self.assertEqual(decoded_ack, ack)
        self.assertTrue(decoded_ack.HasField("change_sampling_interval"))

    def test_standard_error_round_trip_contract(self):
        error = standard_error_pb2.StandardError()
        error.code = standard_error_pb2.ERROR_CODE_VALIDATION_FAILED
        error.message = "validation failed"
        error.source_field = "sequence_number"
        error.metadata["rule"] = "monotonic"

        self.assertEqual(error.code, standard_error_pb2.ERROR_CODE_VALIDATION_FAILED)
        self.assertTrue(error.message)
        self.assertTrue(error.source_field)
        self.assertIn("rule", error.metadata)
        self.assertEqual(error.metadata["rule"], "monotonic")

        payload = error.SerializeToString()
        self.assertGreater(len(payload), 0)

        decoded = standard_error_pb2.StandardError()
        decoded.ParseFromString(payload)
        self.assertEqual(decoded, error)
        self.assertEqual(decoded.metadata["rule"], "monotonic")


if __name__ == "__main__":
    unittest.main()
