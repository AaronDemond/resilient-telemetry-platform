# Canonical validation contract

This document is the single readable specification that both the Python simulator and the C++ ingestion engine must validate against. It is the shared contract for message shape, numeric constraints, timestamp semantics, and cross-field validation.

## Validation boundary

Validation must not live only in the UI or only in one language runtime. The business rules must be enforced in the shared validation boundary used by both implementations.

Required validation points:

- Python simulator before publishing a message to the transport.
- C++ ingestion engine before accepting the event into the event log.
- Shared golden tests that verify identical invalid inputs fail in both languages.

The validation flow is:

1. Parse the message.
2. Check schema-level shape.
3. Check value ranges and enum validity.
4. Check cross-field rules.
5. Reject with a standard error if invalid.

This avoids the common mistake of validating only one language and assuming the other will do the same.

## Envelope identity and required fields

The `Envelope` is the outer wrapper for all telemetry and request traffic. It provides identity, ordering, and trace metadata. The following fields are required for a valid v1 envelope:

- `message_id`
- `run_id`
- `unit_id`
- `boot_id`
- `sequence_number`
- `source_timestamp_ms`
- `schema_version`

`correlation_id` is required for request/response tracing flows and must be carried through the full lifecycle when the message is part of a request-response exchange.

## Numeric and semantic constraints

| Field | Unit | Valid range | Notes |
| --- | --- | --- | --- |
| `fuel_remaining` | percent | 0.0 to 100.0 | Fractional values are allowed if the simulator emits them |
| `equipment_temperature_c` | Celsius | -50.0 to 120.0 | High enough for equipment stress, low enough for cold weather |
| `connectivity_quality` | normalized score | 0.0 to 1.0 | Use `0.0` for no connectivity and `1.0` for perfect connectivity |
| `source_timestamp_ms` | Unix epoch milliseconds | >= 0 | The clock source and timezone behavior must be documented |
| `sequence_number` | count | >= 1 | Monotonic within a unit boot/session |
| `schema_version` | integer | >= 1 | Use increments only for backwards-compatible or explicitly versioned changes |

## Validation principles

- `fuel_remaining` is a percentage, not a raw fraction; values must stay within the stated physical range.
- `equipment_temperature_c` uses Celsius and must remain realistic for field equipment.
- `connectivity_quality` is normalized to the range `[0.0, 1.0]` to keep interpretation consistent across implementations.
- `source_timestamp_ms` must be an epoch-based millisecond value and cannot be negative.
- `sequence_number` must increase monotonically within a boot/session and never restart unexpectedly.
- `schema_version` must be positive and change only when the wire format or validation rules intentionally change.

## Timestamp semantics

- `source_timestamp_ms` is the unit’s local observation time, stored as Unix epoch milliseconds.
- The source timestamp is not the server’s wall-clock time or a “now” value from the receiver. It is the telemetry producer’s own observation.
- The server must reject timestamps that are malformed, negative, or implausibly far in the future relative to the receiving clock.
- The server may accept delayed or out-of-order messages, but only under explicit validation rules that preserve ordering semantics and data quality.

## Sequence semantics

- A sequence number increases strictly within the same `boot_id` for a given `unit_id`.
- A restart creates a new `boot_id`; the sequence number may reset to 1 when the unit boots again.
- A `sequence_number` restart without a new `boot_id` is invalid and must be treated as a protocol violation.
- A sequence gap is not necessarily a fatal error if the system explicitly permits skipped values, but the sequence must remain monotonic within the same boot lifecycle.

## Contract statement

> The telemetry source timestamp is measured in milliseconds since the Unix epoch. Sequence numbers are monotonic within a unit boot/session and reset only after a new `boot_id` is issued. The server rejects timestamps that are not parseable, negative, or implausibly far in the future.

This is the canonical specification that both implementations are expected to validate and test against. Any future change to this contract must be reflected in both implementation validators and the shared golden test suite.
