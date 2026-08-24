# Design rules to lock in now

## Rule 1 — Every enum starts with an UNSPECIFIED value at 0

This is Protocol Buffers convention and it prevents a class of bugs where an unset enum silently maps to a valid state.

## Rule 2 — Field numbers are permanent

Never reuse a field number for a different meaning. If you remove a field, add a `reserved` block:

```
reserved 15;
// or
reserved 15 to 20;
```

## Rule 3 — Use `oneof` for variant payloads, not `optional` on every subtype

`oneof` enforces that exactly one variant is present. Using `optional` on four fields would allow zero or multiple subtypes, which is not what the system needs.

## Rule 4 — Keep `TelemetryEvent` flat, not nested

The telemetry message is sent at high frequency. Flat messages serialize faster and are easier to validate. Nested messages add indirection without benefit here.

## Rule 5 — Use explicit types, not `bytes` or `string` for structured data

`double` for coordinates, `float` for measurements, `uint64` for sequence numbers. Do not store a battery level as a string `"85.3"` — use the numeric type that conveys the semantics.

## Rule 6 — Include `correlation_id` on every request and response

This is the single field that makes end-to-end tracing possible. If it is missing from any message, the lifecycle is broken.

## Rule 7 — Put validation at the shared boundary, not in one runtime

Do not bury all business validation in the UI or in only one implementation language. The validator boundary belongs in the code paths that can be tested and reused across the system.

Validation must happen in at least these places:

- Python simulator before publishing a message to the transport.
- C++ ingestion engine before accepting the event into the event log.
- Shared golden tests that verify identical invalid cases fail in both languages.

The validation pattern should be consistent and explicit:

1. Parse the message.
2. Check schema-level shape.
3. Check value ranges and enum validity.
4. Check cross-field rules.
5. Reject with a standard error if invalid.

This avoids the common mistake of validating only one language and assuming the other will do the same.
