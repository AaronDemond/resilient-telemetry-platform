#include "units_api_v1.h"

#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <functional>
#include <map>
#include <string>

#include <drogon/HttpAppFramework.h>
#include <drogon/HttpResponse.h>
#include <drogon/utils/FunctionTraits.h>
#include <json/json.h>
#include <pqxx/pqxx>

namespace telemetry::api::v1 {
namespace {

void apply_cors_headers(const drogon::HttpResponsePtr& response) {
    response->addHeader("Access-Control-Allow-Origin", "*");
    response->addHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
    response->addHeader("Access-Control-Allow-Headers", "Content-Type");
}

constexpr const char* kDefaultPostgresHost = "127.0.0.1";
constexpr const char* kDefaultPostgresPort = "15432";
constexpr const char* kDefaultPostgresDatabase = "telemetry";
constexpr const char* kDefaultPostgresUser = "telemetry";
constexpr const char* kDefaultPostgresPassword = "password";

std::string trim(std::string value) {
    const auto begin = value.find_first_not_of(" \t\r\n");
    if (begin == std::string::npos) {
        return {};
    }

    const auto end = value.find_last_not_of(" \t\r\n");
    return value.substr(begin, end - begin + 1);
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

std::map<std::string, std::string> load_dotenv_values() {
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

        std::string key = trim(line.substr(0, separator));
        std::string value = trim(line.substr(separator + 1));
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

std::string resolve_setting(
    const std::map<std::string, std::string>& dotenv_values,
    std::initializer_list<const char*> env_names,
    std::initializer_list<const char*> dotenv_names,
    const char* fallback) {
    for (const char* env_name : env_names) {
        if (const char* value = std::getenv(env_name); value != nullptr && value[0] != '\0') {
            return value;
        }
    }

    for (const char* dotenv_name : dotenv_names) {
        const auto it = dotenv_values.find(dotenv_name);
        if (it != dotenv_values.end() && !it->second.empty()) {
            return it->second;
        }
    }

    return fallback;
}

std::string build_postgres_connection_string() {
    const auto dotenv_values = load_dotenv_values();

    const std::string host = resolve_setting(
        dotenv_values,
        {"TELEMETRY_PGHOST", "POSTGRES_HOST"},
        {"TELEMETRY_PGHOST", "POSTGRES_HOST"},
        kDefaultPostgresHost);
    const std::string port = resolve_setting(
        dotenv_values,
        {"TELEMETRY_PGPORT", "POSTGRES_PORT"},
        {"TELEMETRY_PGPORT", "POSTGRES_PORT"},
        kDefaultPostgresPort);
    const std::string dbname = resolve_setting(
        dotenv_values,
        {"TELEMETRY_PGDATABASE", "POSTGRES_DB"},
        {"TELEMETRY_PGDATABASE", "POSTGRES_DB"},
        kDefaultPostgresDatabase);
    const std::string user = resolve_setting(
        dotenv_values,
        {"TELEMETRY_PGUSER", "POSTGRES_USER"},
        {"TELEMETRY_PGUSER", "POSTGRES_USER"},
        kDefaultPostgresUser);
    const std::string password = resolve_setting(
        dotenv_values,
        {"TELEMETRY_PGPASSWORD", "POSTGRES_PASSWORD"},
        {"TELEMETRY_PGPASSWORD", "POSTGRES_PASSWORD"},
        kDefaultPostgresPassword);

    return "host=" + host + " port=" + port + " dbname=" + dbname + " user=" + user + " password=" + password;
}

template <typename RowLike>
Json::Value row_to_json(const RowLike& row) {
    Json::Value item(Json::objectValue);

    item["id"] = static_cast<Json::Value::Int64>(row["id"].as<long long>());
    item["received_at"] = row["received_at"].as<std::string>();
    item["message_id"] = row["message_id"].as<std::string>();
    item["run_id"] = row["run_id"].as<std::string>();
    item["unit_id"] = row["unit_id"].as<std::string>();
    item["boot_id"] = row["boot_id"].as<std::string>();
    item["session_id"] = row["session_id"].as<std::string>();
    item["sequence_number"] = static_cast<Json::Value::Int64>(row["sequence_number"].as<long long>());
    item["source_timestamp_ms"] = static_cast<Json::Value::Int64>(row["source_timestamp_ms"].as<long long>());
    item["schema_version"] = row["schema_version"].as<int>();
    item["correlation_id"] = row["correlation_id"].as<std::string>();
    item["software_version"] = row["software_version"].as<std::string>();
    item["latitude"] = row["latitude"].as<double>();
    item["longitude"] = row["longitude"].as<double>();
    item["fuel_remaining"] = row["fuel_remaining"].as<double>();
    item["equipment_temperature_c"] = row["equipment_temperature_c"].as<double>();
    item["connectivity_quality"] = row["connectivity_quality"].as<double>();
    item["temperature_warning"] = row["temperature_warning"].as<bool>();
    item["connectivity_degraded"] = row["connectivity_degraded"].as<bool>();
    item["maintenance_required"] = row["maintenance_required"].as<bool>();
    item["status"] = row["status"].as<int>();

    return item;
}

}  // namespace

void UnitsController::get_units(
    const drogon::HttpRequestPtr& req,
    std::function<void(const drogon::HttpResponsePtr&)>&& callback) {
    if (req->method() == drogon::Options) {
        auto response = drogon::HttpResponse::newHttpResponse();
        response->setStatusCode(drogon::k204NoContent);
        apply_cors_headers(response);
        callback(response);
        return;
    }

    try {
        const std::string requested_run_id = req->getParameter("run_id");
        const std::string requested_unit_id = req->getParameter("id");

        pqxx::connection database{build_postgres_connection_string()};

        std::string query = R"sql(
            SELECT
                id,
                received_at,
                message_id,
                run_id,
                unit_id,
                boot_id,
                COALESCE(session_id, '') AS session_id,
                sequence_number,
                source_timestamp_ms,
                schema_version,
                COALESCE(correlation_id, '') AS correlation_id,
                software_version,
                latitude,
                longitude,
                fuel_remaining,
                equipment_temperature_c,
                connectivity_quality,
                temperature_warning,
                connectivity_degraded,
                maintenance_required,
                status
            FROM telemetry_messages
        )sql";

        pqxx::result rows;
        pqxx::work transaction{database};
        if (requested_run_id.empty()) {
            query += " WHERE 1 = 0";
            rows = transaction.exec(query);
        } else if (requested_unit_id.empty()) {
            query += " WHERE run_id = $1 ORDER BY received_at DESC";
            rows = transaction.exec_params(query, requested_run_id);
        } else {
            query += " WHERE run_id = $1 AND unit_id = $2 ORDER BY received_at DESC";
            rows = transaction.exec_params(query, requested_run_id, requested_unit_id);
        }
        transaction.commit();

        Json::Value payload(Json::arrayValue);
        for (const auto& row : rows) {
            payload.append(row_to_json(row));
        }

        auto response = drogon::HttpResponse::newHttpJsonResponse(payload);
        response->setStatusCode(drogon::k200OK);
        apply_cors_headers(response);
        callback(response);
    } catch (const std::exception& error) {
        Json::Value error_payload(Json::objectValue);
        error_payload["error"] = error.what();

        auto response = drogon::HttpResponse::newHttpJsonResponse(error_payload);
        response->setStatusCode(drogon::k500InternalServerError);
        apply_cors_headers(response);
        callback(response);
    }
}

}  // namespace telemetry::api::v1
