# Envelope record

Example of the right kind of record:

> The `Envelope` message is the shared wrapper for all telemetry and request traffic. It contains `message_id`, `unit_id`, `boot_id`, `sequence_number`, `source_timestamp_ms`, `schema_version`, `correlation_id`, and `run_id`. These fields are used for routing, deduplication, ordering, and correlation. The payload messages are defined in Step 2 and the legal values and units are defined in Step 3.

This summary becomes the bridge between the implementation and the requirements baseline.
