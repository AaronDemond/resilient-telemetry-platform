#include "ingest.hpp"

#include <chrono>
#include <condition_variable>
#include <cstdio>
#include <cstdlib>
#include <deque>
#include <exception>
#include <filesystem>
#include <fstream>
#include <map>
#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <thread>
#include <utility>
#include <vector>

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

struct QueuedMessage {
    MessageHandle message;
};

class MessageQueue {
public:
    void push(QueuedMessage message) {
        std::lock_guard lock(mutex_);
        if (shutdown_) {
            return;
        }
        queue_.push_back(std::move(message));
        condition_.notify_one();
    }

    std::optional<QueuedMessage> pop() {
        std::unique_lock lock(mutex_);
        condition_.wait(lock, [this] { return shutdown_ || !queue_.empty(); });
        if (queue_.empty()) {
            return std::nullopt;
        }

        QueuedMessage next = std::move(queue_.front());
        queue_.pop_front();
        return next;
    }

    void close() {
        {
            std::lock_guard lock(mutex_);
            shutdown_ = true;
        }
        condition_.notify_all();
    }

private:
    std::mutex mutex_;
    std::condition_variable condition_;
    std::deque<QueuedMessage> queue_;
    bool shutdown_ = false;
};

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

        if (value.size() >= 2 && value.front() == '"' && value.back() == '"') {
            value = value.substr(1, value.size() - 2);
        }

        values.emplace(std::move(key), std::move(value));
    }

    return values;
}

std::string resolve_postgres_setting(
    const std::map<std::string, std::string>& dotenv_values,
    const char* const* env_names,
    std::size_t env_name_count,
    const char* const* dotenv_names,
    std::size_t dotenv_name_count,
    const char* fallback) {
    for (std::size_t i = 0; i < dotenv_name_count; ++i) {
        const char* dotenv_name = dotenv_names[i];
        const auto it = dotenv_values.find(dotenv_name);
        if (it != dotenv_values.end() && !it->second.empty()) {
            return it->second;
        }
    }

    for (std::size_t i = 0; i < env_name_count; ++i) {
        const char* env_name = env_names[i];
        if (const char* value = std::getenv(env_name); value != nullptr && value[0] != '\0') {
            return value;
        }
    }

    return fallback;
}

std::map<std::string, std::string> build_postgres_connection_params() {
    const auto dotenv_values = load_dotenv_settings();
    std::map<std::string, std::string> params;

    const char* host_env_names[] = {"TELEMETRY_PGHOST", "POSTGRES_HOST"};
    const char* host_dotenv_names[] = {"TELEMETRY_PGHOST", "POSTGRES_HOST"};
    params.emplace(
        "host",
        resolve_postgres_setting(
            dotenv_values,
            host_env_names,
            2,
            host_dotenv_names,
            2,
            kDefaultPostgresHost));

    const char* port_env_names[] = {"TELEMETRY_PGPORT", "POSTGRES_PORT"};
    const char* port_dotenv_names[] = {"TELEMETRY_PGPORT", "POSTGRES_PORT"};
    params.emplace(
        "port",
        resolve_postgres_setting(
            dotenv_values,
            port_env_names,
            2,
            port_dotenv_names,
            2,
            kDefaultPostgresPort));

    const char* dbname_env_names[] = {"TELEMETRY_PGDATABASE", "POSTGRES_DB"};
    const char* dbname_dotenv_names[] = {"TELEMETRY_PGDATABASE", "POSTGRES_DB"};
    params.emplace(
        "dbname",
        resolve_postgres_setting(
            dotenv_values,
            dbname_env_names,
            2,
            dbname_dotenv_names,
            2,
            kDefaultPostgresDatabase));

    const char* user_env_names[] = {"TELEMETRY_PGUSER", "POSTGRES_USER"};
    const char* user_dotenv_names[] = {"TELEMETRY_PGUSER", "POSTGRES_USER"};
    params.emplace(
        "user",
        resolve_postgres_setting(
            dotenv_values,
            user_env_names,
            2,
            user_dotenv_names,
            2,
            kDefaultPostgresUser));

    const char* password_env_names[] = {"TELEMETRY_PGPASSWORD", "POSTGRES_PASSWORD"};
    const char* password_dotenv_names[] = {"TELEMETRY_PGPASSWORD", "POSTGRES_PASSWORD"};
    params.emplace(
        "password",
        resolve_postgres_setting(
            dotenv_values,
            password_env_names,
            2,
            password_dotenv_names,
            2,
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

        std::fprintf(stderr, "js_UpdateStream failed for %s; deleting stale stream and recreating it.\n", stream_name);
    }

    status = js_AddStream(nullptr, js, &stream_config, nullptr, nullptr);
    if (status == NATS_OK || js_GetStreamInfo(nullptr, js, stream_name, nullptr, nullptr) == NATS_OK) {
        return true;
    }

    std::fprintf(stderr, "js_AddStream failed for %s; deleting stale stream and recreating it.\n", stream_name);
    js_DeleteStream(js, stream_name, nullptr, nullptr);

    status = js_AddStream(nullptr, js, &stream_config, nullptr, nullptr);
    if (status == NATS_OK || js_GetStreamInfo(nullptr, js, stream_name, nullptr, nullptr) == NATS_OK) {
        return true;
    }

    report_status("js_AddStream", status);
    return false;
}

void worker_loop(MessageQueue& queue, pqxx::connection& database) {
    while (true) {
        const auto message = queue.pop();
        if (!message.has_value()) {
            return;
        }

        QueuedMessage queued = std::move(message.value());
        if (!queued.message || !queued.message.get()) {
            continue;
        }

        try {
            const char* payload_data = natsMsg_GetData(queued.message.get());
            const int payload_length = natsMsg_GetDataLength(queued.message.get());
            if (payload_data == nullptr || payload_length <= 0) {
                std::fprintf(stderr, "Received an empty telemetry payload\n");
                continue;
            }

            const std::string payload(payload_data, static_cast<std::size_t>(payload_length));
            const auto telemetry_data = telemetry::core::TelemetryData::deserialize(payload);
            telemetry::adapters::postgres::store_telemetry_message(database, telemetry_data, payload);

            const natsStatus ack_status = natsMsg_AckSync(queued.message.get(), nullptr, nullptr);
            if (ack_status != NATS_OK) {
                report_status("natsMsg_AckSync", ack_status);
                continue;
            }

            const auto telemetry_message = telemetry_data.to_proto();
            std::printf(
                "Stored telemetry message on %s for unit %s:\n%s\n",
                natsMsg_GetSubject(queued.message.get()),
                telemetry_data.unit_id().c_str(),
                telemetry_message.DebugString().c_str());
        } catch (const std::exception& error) {
            std::fprintf(stderr, "Failed to decode or store telemetry payload: %s\n", error.what());
        }
    }
}

void receiver_loop(MessageQueue& queue, natsSubscription* subscription) {
    while (true) {
        natsMsg* raw_message = nullptr;
        const natsStatus status = natsSubscription_NextMsg(&raw_message, subscription, 30000);
        if (status == NATS_TIMEOUT) {
            continue;
        }

        if (status != NATS_OK) {
            report_status("natsSubscription_NextMsg", status);
            queue.close();
            return;
        }

        if (raw_message == nullptr) {
            continue;
        }

        queue.push(QueuedMessage{MessageHandle(raw_message, natsMsg_Destroy)});
    }
}

}  // namespace

int run_ingestor(const char* nats_url, const char* stream_name, const char* subject, std::size_t worker_count) {
    ConnectionHandle connection(nullptr, natsConnection_Destroy);
    JetStreamHandle jetstream(nullptr, jsCtx_Destroy);

    try {
        natsConnection* raw_connection = nullptr;
        const natsStatus connect_status = natsConnection_ConnectTo(&raw_connection, nats_url);
        if (connect_status != NATS_OK) {
            report_status("natsConnection_ConnectTo", connect_status);
            return 1;
        }

        connection.reset(raw_connection);

        jsCtx* raw_jetstream = nullptr;
        const natsStatus jetstream_status = natsConnection_JetStream(&raw_jetstream, connection.get(), nullptr);
        if (jetstream_status != NATS_OK) {
            report_status("natsConnection_JetStream", jetstream_status);
            return 1;
        }

        jetstream.reset(raw_jetstream);

        if (!ensure_test_stream(jetstream.get(), stream_name, subject)) {
            return 1;
        }

        jsSubOptions sub_options;
        const natsStatus sub_options_status = jsSubOptions_Init(&sub_options);
        if (sub_options_status != NATS_OK) {
            report_status("jsSubOptions_Init", sub_options_status);
            return 1;
        }

        sub_options.Stream = stream_name;
        sub_options.Config.Durable = kTelemetryConsumerName;
        sub_options.Config.DeliverPolicy = js_DeliverNew;
        sub_options.Config.AckPolicy = js_AckExplicit;
        sub_options.ManualAck = true;

        SubscriptionHandle subscription(nullptr, natsSubscription_Destroy);
        natsSubscription* raw_subscription = nullptr;
        const natsStatus subscribe_status = js_SubscribeSync(
            &raw_subscription,
            jetstream.get(),
            subject,
            nullptr,
            &sub_options,
            nullptr);
        if (subscribe_status != NATS_OK) {
            report_status("js_SubscribeSync", subscribe_status);
            return 1;
        }
        subscription.reset(raw_subscription);

        MessageQueue queue;
        const std::size_t actual_workers = worker_count == 0 ? 1U : worker_count;
        std::vector<std::unique_ptr<pqxx::connection>> worker_connections;
        worker_connections.reserve(actual_workers);
        for (std::size_t index = 0; index < actual_workers; ++index) {
            worker_connections.emplace_back(std::make_unique<pqxx::connection>(build_postgres_connection_params()));
            telemetry::adapters::postgres::ensure_telemetry_schema(*worker_connections.back());
        }

        std::vector<std::thread> workers;
        workers.reserve(actual_workers);
        for (std::size_t index = 0; index < actual_workers; ++index) {
            workers.emplace_back(worker_loop, std::ref(queue), std::ref(*worker_connections[index]));
        }

        std::thread receiver(receiver_loop, std::ref(queue), subscription.get());
        std::printf("Listening for telemetry on %s with %zu workers...\n", subject, actual_workers);

        while (true) {
            std::this_thread::sleep_for(std::chrono::seconds(1));
        }
    } catch (const std::exception& error) {
        std::fprintf(stderr, "Ingestor failed: %s\n", error.what());
        return 1;
    }
}

}  // namespace telemetry::ingestor
