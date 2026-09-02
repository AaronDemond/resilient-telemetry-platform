#include "telemetry/postgres/postgres_adapter.hpp"

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

#include <pqxx/pqxx>

#include "telemetry/core/telemetry_data.hpp"

namespace telemetry::adapters::postgres {
namespace {

std::string optional_text_literal(pqxx::work& transaction, std::string_view value) {
    if (value.empty()) {
        return "NULL";
    }

    return transaction.quote(value);
}

pqxx::bytes_view raw_payload_view(std::string_view raw_payload) {
    return pqxx::bytes_view{
        reinterpret_cast<std::byte const*>(raw_payload.data()), raw_payload.size()};
}

}  // namespace

const char* adapter_name() noexcept {
    return "postgres";
}

void ensure_telemetry_schema(pqxx::connection& connection) {
    pqxx::work transaction{connection};

    transaction.exec(R"sql(
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
        )
    )sql");

    transaction.exec(R"sql(
        CREATE INDEX IF NOT EXISTS telemetry_messages_message_id_idx
            ON telemetry_messages (message_id)
    )sql");

    transaction.exec(R"sql(
        CREATE INDEX IF NOT EXISTS telemetry_messages_run_received_at_idx
            ON telemetry_messages (run_id, received_at DESC)
    )sql");

    transaction.exec(R"sql(
        CREATE INDEX IF NOT EXISTS telemetry_messages_unit_boot_sequence_idx
            ON telemetry_messages (unit_id, boot_id, sequence_number)
    )sql");

    transaction.exec(R"sql(
        CREATE INDEX IF NOT EXISTS telemetry_messages_received_at_idx
            ON telemetry_messages (received_at DESC)
    )sql");

    transaction.commit();
}

void store_telemetry_message(
    pqxx::connection& connection,
    const telemetry::core::TelemetryData& telemetry,
    std::string_view raw_payload) {
    pqxx::work transaction{connection};

    std::string insert_sql;
    insert_sql.reserve(1024);
    insert_sql += "INSERT INTO telemetry_messages (";
    insert_sql +=
        "message_id, run_id, unit_id, boot_id, session_id, sequence_number, source_timestamp_ms, "
        "schema_version, correlation_id, software_version, latitude, longitude, fuel_remaining, "
        "equipment_temperature_c, connectivity_quality, temperature_warning, connectivity_degraded, "
        "maintenance_required, status, raw_payload) VALUES (";
    insert_sql += transaction.quote(telemetry.message_id());
    insert_sql += ", ";
    insert_sql += transaction.quote(telemetry.run_id());
    insert_sql += ", ";
    insert_sql += transaction.quote(telemetry.unit_id());
    insert_sql += ", ";
    insert_sql += transaction.quote(telemetry.boot_id());
    insert_sql += ", ";
    insert_sql += optional_text_literal(transaction, telemetry.session_id());
    insert_sql += ", ";
    insert_sql += transaction.quote(telemetry.sequence_number());
    insert_sql += ", ";
    insert_sql += transaction.quote(telemetry.source_timestamp_ms());
    insert_sql += ", ";
    insert_sql += transaction.quote(telemetry.schema_version());
    insert_sql += ", ";
    insert_sql += optional_text_literal(transaction, telemetry.correlation_id());
    insert_sql += ", ";
    insert_sql += transaction.quote(telemetry.software_version());
    insert_sql += ", ";
    insert_sql += transaction.quote(telemetry.latitude());
    insert_sql += ", ";
    insert_sql += transaction.quote(telemetry.longitude());
    insert_sql += ", ";
    insert_sql += transaction.quote(telemetry.fuel_remaining());
    insert_sql += ", ";
    insert_sql += transaction.quote(telemetry.equipment_temperature_c());
    insert_sql += ", ";
    insert_sql += transaction.quote(telemetry.connectivity_quality());
    insert_sql += ", ";
    insert_sql += telemetry.temperature_warning() ? "TRUE" : "FALSE";
    insert_sql += ", ";
    insert_sql += telemetry.connectivity_degraded() ? "TRUE" : "FALSE";
    insert_sql += ", ";
    insert_sql += telemetry.maintenance_required() ? "TRUE" : "FALSE";
    insert_sql += ", ";
    insert_sql += transaction.quote(static_cast<std::int32_t>(telemetry.status()));
    insert_sql += ", ";
    insert_sql += connection.quote_raw(raw_payload_view(raw_payload));
    insert_sql += ")";

    transaction.exec(insert_sql);
    transaction.commit();
}

}  // namespace telemetry::adapters::postgres