# Message and field purpose record

## TelemetryEvent

| Field | Type | Purpose |
| --- | --- | --- |
| `unit_id` | `string` | Identifies the physical unit |
| `boot_id` | `string` | Session identity for deduplication |
| `schema_version` | `uint32` | Allows version-specific validation |
| `software_version` | `string` | Records the unit's firmware version |
| `sequence_number` | `uint64` | Per-boot monotonic ordering key |
| `source_timestamp_ms` | `int64` | When the unit recorded the measurement |
| `latitude` / `longitude` | `double` | Position on a synthetic coordinate plane |
| `fuel_remaining` | `float` | Remaining fuel percentage |
| `equipment_temperature_c` | `float` | Sensor temperature in Celsius |
| `connectivity_quality` | `float` | Signal quality indicator |
| `health_flags` | `HealthFlags` | Structured boolean health indicators |
| `status` | `UnitStatus` | Mission-neutral unit state |
| `correlation_id` | `string` | Links this telemetry to an operator request if applicable |

## OperatorRequest

| Field | Type | Purpose |
| --- | --- | --- |
| `request_id` | `string` | Unique identifier for this request |
| `unit_id` | `string` | Target unit |
| `boot_id` | `string` | Target boot session |
| `correlation_id` | `string` | End-to-end traceability ID |
| `oneof request_type` | varies | Exactly one of the four request subtypes |

## RequestAcknowledgement

| Field | Type | Purpose |
| --- | --- | --- |
| `request_id` | `string` | Matches the original request |
| `unit_id` | `string` | Responding unit |
| `boot_id` | `string` | Boot session at time of response |
| `correlation_id` | `string` | End-to-end traceability ID |
| `status` | `AcknowledgementStatus` | Applied, rejected, or not supported |
| `oneof response` | varies | Request-specific response payload |

## StandardError

| Field | Type | Purpose |
| --- | --- | --- |
| `code` | `ErrorCode` | Machine-readable error category |
| `message` | `string` | Human-readable description |
| `source_field` | `string` | Which field caused the error |
| `metadata` | `map<string, string>` | Additional key-value context |

This record is a design review artifact for reviewers. It explains why each field exists and how each message serves the protocol without duplicating the implementation details already in the `.proto` files.
