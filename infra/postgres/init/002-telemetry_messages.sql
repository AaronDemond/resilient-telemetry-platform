CREATE TABLE IF NOT EXISTS telemetry_messages (
    id bigserial PRIMARY KEY,
    received_at timestamptz NOT NULL DEFAULT now(),
    message_id text NOT NULL,
    run_id text NOT NULL,
    unit_id text NOT NULL,
    boot_id text NOT NULL,
    session_id text,
    sequence_number bigint NOT NULL,
    source_timestamp_ms bigint NOT NULL,
    schema_version integer NOT NULL,
    correlation_id text,
    software_version text NOT NULL,
    latitude double precision NOT NULL,
    longitude double precision NOT NULL,
    fuel_remaining real NOT NULL,
    equipment_temperature_c real NOT NULL,
    connectivity_quality real NOT NULL,
    temperature_warning boolean NOT NULL,
    connectivity_degraded boolean NOT NULL,
    maintenance_required boolean NOT NULL,
    status integer NOT NULL,
    raw_payload bytea NOT NULL
);

CREATE INDEX IF NOT EXISTS telemetry_messages_message_id_idx
    ON telemetry_messages (message_id);

CREATE INDEX IF NOT EXISTS telemetry_messages_unit_boot_sequence_idx
    ON telemetry_messages (unit_id, boot_id, sequence_number);

CREATE INDEX IF NOT EXISTS telemetry_messages_received_at_idx
    ON telemetry_messages (received_at DESC);