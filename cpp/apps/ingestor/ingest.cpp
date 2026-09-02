#include "ingest.hpp"

#include <cstdio>
#include <cstdlib>
#include <exception>
#include <filesystem>
#include <fstream>
#include <map>
#include <memory>
#include <string>

#include <pqxx/pqxx>

#include "nats/nats.h"
#include "telemetry/core/telemetry_data.hpp"
#include "telemetry/postgres/postgres_adapter.hpp"

namespace telemetry::ingestor {
namespace {

constexpr const char* kDefaultNatsUrl = "nats://127.0.0.1:14222";
constexpr const char* kDefaultStreamName = "TELEMETRY_TEST_STREAM";
constexpr const char* kDefaultSubject = "telemetry.test.ingestor";
constexpr const char* kTelemetryConsumerName = "telemetry_ingestor";
constexpr const char* kDefaultPostgresHost = "127.0.0.1";
constexpr const char* kDefaultPostgresPort = "15432";
constexpr const char* kDefaultPostgresDatabase = "telemetry";
constexpr const char* kDefaultPostgresUser = "telemetry";
constexpr const char* kDefaultPostgresPassword = "password";

using ConnectionHandle = std::unique_ptr<natsConnection, void (*)(natsConnection*)>;
using JetStreamHandle = std::unique_ptr<jsCtx, void (*)(jsCtx*)>;
using SubscriptionHandle = std::unique_ptr<natsSubscription, void (*)(natsSubscription*)>;
using MessageHandle = std::unique_ptr<natsMsg, void (*)(natsMsg*)>;

const char* env_or_default(const char* name, const char* fallback) noexcept {
    if (const char* value = std::getenv(name); value != nullptr && value[0] != '\0') {
        return value;
    }

    return fallback;
}

std::string trim(const std::string& value) {
    const auto start = value.find_first_not_of(" \t\r\n");
    if (start == std::string::npos) {
        return {};
    }

    const auto end = value.find_last_not_of(" \t\r\n");
    return value.substr(start, end - start + 1);
}

std::filesystem::path find_project_dotenv() {
    std::filesystem::path probe = std::filesystem::current_path();
    while (true) {
        const auto local_dotenv = probe / ".env";
        if (std::filesystem::exists(local_dotenv) && std::filesystem::is_regular_file(local_dotenv)) {
            return local_dotenv;
        }

        const auto parent = probe.parent_path();
        if (parent == probe) {
            break;
        }

        probe = parent;
    }

    return {};
}

std::map<std::string, std::string> load_dotenv_settings() {
    std::map<std::string, std::string> values;
    const auto dotenv_path = find_project_dotenv();
    if (dotenv_path.empty()) {
        return values;
    }

    std::ifstream dotenv_file(dotenv_path);
    if (!dotenv_file.is_open()) {
        return values;
    }

    std::string line;
    while (std::getline(dotenv_file, line)) {
        const auto separator = line.find('=');
        if (separator == std::string::npos) {
            continue;
        }

        auto key = trim(line.substr(0, separator));
        auto value = trim(line.substr(separator + 1));
        if (key.empty()) {
            continue;
        }

        // Allow quoted values like "password" without changing the actual secret.
        if (value.size() >= 2 && value.front() == '"' && value.back() == '"') {
            value = value.substr(1, value.size() - 2);
        }

        values.emplace(std::move(key), std::move(value));
    }

    return values;
}

std::string resolve_postgres_setting(
    const std::map<std::string, std::string>& dotenv_values,
    std::initializer_list<const char*> env_names,
    std::initializer_list<const char*> dotenv_names,
    const char* fallback) {
    // Prefer the repo-local connection settings so stale shells cannot redirect ingestion.
    for (const char* dotenv_name : dotenv_names) {
        const auto it = dotenv_values.find(dotenv_name);
        if (it != dotenv_values.end() && !it->second.empty()) {
            return it->second;
        }
    }

    for (const char* env_name : env_names) {
        if (const char* value = std::getenv(env_name); value != nullptr && value[0] != '\0') {
            return value;
        }
    }

    return fallback;
}

std::map<std::string, std::string> build_postgres_connection_params() {
    const auto dotenv_values = load_dotenv_settings();
    std::map<std::string, std::string> params;
    params.emplace(
        "host",
        resolve_postgres_setting(
            dotenv_values,
            {"TELEMETRY_PGHOST", "POSTGRES_HOST"},
            {"TELEMETRY_PGHOST", "POSTGRES_HOST"},
            kDefaultPostgresHost));
    params.emplace(
        "port",
        resolve_postgres_setting(
            dotenv_values,
            {"TELEMETRY_PGPORT", "POSTGRES_PORT"},
            {"TELEMETRY_PGPORT", "POSTGRES_PORT"},
            kDefaultPostgresPort));
    params.emplace(
        "dbname",
        resolve_postgres_setting(
            dotenv_values,
            {"TELEMETRY_PGDATABASE", "POSTGRES_DB"},
            {"TELEMETRY_PGDATABASE", "POSTGRES_DB"},
            kDefaultPostgresDatabase));
    params.emplace(
        "user",
        resolve_postgres_setting(
            dotenv_values,
            {"TELEMETRY_PGUSER", "POSTGRES_USER"},
            {"TELEMETRY_PGUSER", "POSTGRES_USER"},
            kDefaultPostgresUser));
    params.emplace(
        "password",
        resolve_postgres_setting(
            dotenv_values,
            {"TELEMETRY_PGPASSWORD", "POSTGRES_PASSWORD"},
            {"TELEMETRY_PGPASSWORD", "POSTGRES_PASSWORD"},
            kDefaultPostgresPassword));
    return params;
}

void report_status(const char* action, natsStatus status) {
    std::fprintf(stderr, "%s failed: %s\n", action, natsStatus_GetText(status));
}

bool ensure_test_stream(jsCtx* js, const char* stream_name, const char* subject) {
    jsStreamConfig stream_config;
    natsStatus status = jsStreamConfig_Init(&stream_config);
    if (status != NATS_OK) {
        report_status("jsStreamConfig_Init", status);
        return false;
    }

    const char* subjects[] = {subject};
    stream_config.Name = stream_name;
    stream_config.Subjects = subjects;
    stream_config.SubjectsLen = 1;
    stream_config.Retention = js_LimitsPolicy;
    stream_config.Discard = js_DiscardOld;
    stream_config.Storage = js_FileStorage;
    stream_config.Replicas = 1;
    stream_config.MaxMsgs = -1;
    stream_config.MaxBytes = -1;

    const bool stream_exists = js_GetStreamInfo(nullptr, js, stream_name, nullptr, nullptr) == NATS_OK;
    if (stream_exists) {
        status = js_UpdateStream(nullptr, js, &stream_config, nullptr, nullptr);
        if (status == NATS_OK || js_GetStreamInfo(nullptr, js, stream_name, nullptr, nullptr) == NATS_OK) {
            return true;
        }

        std::fprintf(
            stderr,
            "js_UpdateStream failed for %s; deleting stale stream and recreating it.\n",
            stream_name);
    }

    status = js_AddStream(nullptr, js, &stream_config, nullptr, nullptr);
    if (status == NATS_OK || js_GetStreamInfo(nullptr, js, stream_name, nullptr, nullptr) == NATS_OK) {
        return true;
    }

    std::fprintf(
        stderr,
        "js_AddStream failed for %s; deleting stale stream and recreating it.\n",
        stream_name);
    js_DeleteStream(js, stream_name, nullptr, nullptr);

    status = js_AddStream(nullptr, js, &stream_config, nullptr, nullptr);
    if (status == NATS_OK || js_GetStreamInfo(nullptr, js, stream_name, nullptr, nullptr) == NATS_OK) {
        return true;
    }

    report_status("js_AddStream", status);
    return false;
}

bool receive_store_and_print_message(
    natsSubscription* subscription,
    pqxx::connection& database) {
    MessageHandle message(nullptr, natsMsg_Destroy);
    natsMsg* raw_message = nullptr;
    natsStatus status = natsSubscription_NextMsg(&raw_message, subscription, 30000);
    if (status == NATS_TIMEOUT) {
        // A timeout means the ingestor is still alive but no message arrived yet.
        // Keep waiting for the next telemetry message instead of shutting down.
        return true;
    }
    if (status != NATS_OK) {
        report_status("natsSubscription_NextMsg", status);
        return false;
    }

    message.reset(raw_message);

    const char* payload_data = natsMsg_GetData(message.get());
    const int payload_length = natsMsg_GetDataLength(message.get());
    if (payload_data == nullptr || payload_length <= 0) {
        std::fprintf(stderr, "Received an empty telemetry payload\n");
        return false;
    }

    try {
        const std::string payload(payload_data, static_cast<std::size_t>(payload_length));
        const auto telemetry_data = telemetry::core::TelemetryData::deserialize(payload);

        telemetry::adapters::postgres::store_telemetry_message(database, telemetry_data, payload);

        // Acknowledge only after Postgres commits so unpersisted messages are redelivered.
        status = natsMsg_AckSync(message.get(), nullptr, nullptr);
        if (status != NATS_OK) {
            report_status("natsMsg_AckSync", status);
            return false;
        }

        const auto telemetry_message = telemetry_data.to_proto();
        std::printf(
            "Stored telemetry message on %s for unit %s:\n%s\n",
            natsMsg_GetSubject(message.get()),
            telemetry_data.unit_id().c_str(),
            telemetry_message.DebugString().c_str());
        return true;
    } catch (const std::exception& error) {
        std::fprintf(stderr, "Failed to decode or store telemetry payload: %s\n", error.what());
        return false;
    }
}

}  // namespace

int run_ingestor(const char* nats_url, const char* stream_name, const char* subject) {
    ConnectionHandle connection(nullptr, natsConnection_Destroy);
    JetStreamHandle jetstream(nullptr, jsCtx_Destroy);

    try {
        natsConnection* raw_connection = nullptr;
        natsStatus status = natsConnection_ConnectTo(&raw_connection, nats_url);
        if (status != NATS_OK) {
            report_status("natsConnection_ConnectTo", status);
            return 1;
        }

        connection.reset(raw_connection);

        pqxx::connection database{build_postgres_connection_params()};
        telemetry::adapters::postgres::ensure_telemetry_schema(database);

        jsCtx* raw_jetstream = nullptr;
        status = natsConnection_JetStream(&raw_jetstream, connection.get(), nullptr);
        if (status != NATS_OK) {
            report_status("natsConnection_JetStream", status);
            return 1;
        }

        jetstream.reset(raw_jetstream);

        if (!ensure_test_stream(jetstream.get(), stream_name, subject)) {
            return 1;
        }

        jsSubOptions sub_options;
        status = jsSubOptions_Init(&sub_options);
        if (status != NATS_OK) {
            report_status("jsSubOptions_Init", status);
            return 1;
        }

        // One durable subscription remains active between messages and restarts.
        sub_options.Stream = stream_name;
        sub_options.Config.Durable = kTelemetryConsumerName;
        sub_options.Config.DeliverPolicy = js_DeliverNew;
        sub_options.Config.AckPolicy = js_AckExplicit;
        sub_options.ManualAck = true;

        SubscriptionHandle subscription(nullptr, natsSubscription_Destroy);
        natsSubscription* raw_subscription = nullptr;
        status = js_SubscribeSync(
            &raw_subscription,
            jetstream.get(),
            subject,
            nullptr,
            &sub_options,
            nullptr);
        if (status != NATS_OK) {
            report_status("js_SubscribeSync", status);
            return 1;
        }
        subscription.reset(raw_subscription);

        std::printf("Listening for telemetry on %s...\n", subject);
        while (true) {
            // Retain this subscription to avoid missing publishes between receive calls.
            const bool ok = receive_store_and_print_message(subscription.get(), database);
            if (!ok) {
                std::fprintf(stderr, "Message ingest loop failed; continuing to listen for new messages.\n");
            }
        }
    } catch (const std::exception& error) {
        std::fprintf(stderr, "Ingestor failed: %s\n", error.what());
        return 1;
    }
}

}  // namespace telemetry::ingestor
