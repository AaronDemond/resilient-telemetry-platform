#include <algorithm>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <string>

#include "ingest.hpp"

namespace {

constexpr const char* kDefaultNatsUrl = "nats://127.0.0.1:14222";
constexpr const char* kDefaultStreamName = "TELEMETRY_TEST_STREAM";
constexpr const char* kDefaultSubject = "telemetry.test.ingestor";

std::string trim(const std::string& value) {
    const auto start = value.find_first_not_of(" \t\r\n");
    if (start == std::string::npos) {
        return {};
    }

    const auto end = value.find_last_not_of(" \t\r\n");
    return value.substr(start, end - start + 1);
}

std::map<std::string, std::string> load_dotenv_settings() {
    std::map<std::string, std::string> values;
    std::filesystem::path directory = std::filesystem::current_path();
    while (true) {
        const auto dotenv_path = directory / ".env";
        if (std::ifstream dotenv_file{dotenv_path}; dotenv_file.is_open()) {
            std::string line;
            while (std::getline(dotenv_file, line)) {
                const auto separator = line.find('=');
                if (separator == std::string::npos) {
                    continue;
                }

                const auto key = trim(line.substr(0, separator));
                const auto value = trim(line.substr(separator + 1));
                if (!key.empty() && !value.empty()) {
                    values.emplace(key, value);
                }
            }
            return values;
        }

        const auto parent = directory.parent_path();
        if (parent == directory) {
            return values;
        }
        directory = parent;
    }
}

std::string resolve_setting(
    const std::map<std::string, std::string>& dotenv_values,
    const char* name,
    const char* fallback) {
    // The repo-local configuration keeps simulator and ingestor endpoints aligned.
    if (const auto it = dotenv_values.find(name); it != dotenv_values.end()) {
        return it->second;
    }

    if (const char* value = std::getenv(name); value != nullptr && value[0] != '\0') {
        return value;
    }

    return fallback;
}

}  // namespace

int main() {
    const auto dotenv_values = load_dotenv_settings();
    const auto nats_url = resolve_setting(dotenv_values, "TELEMETRY_NATS_URL", kDefaultNatsUrl);
    const auto stream_name = resolve_setting(dotenv_values, "TELEMETRY_TEST_STREAM", kDefaultStreamName);
    const auto subject = resolve_setting(dotenv_values, "TELEMETRY_TEST_SUBJECT", kDefaultSubject);
    const auto worker_count_raw = resolve_setting(dotenv_values, "TELEMETRY_INGEST_WORKERS", "4");
    const auto worker_count = std::max(1, std::stoi(worker_count_raw));

    std::cout << "Ingestor configured for " << nats_url << " / " << stream_name << " / " << subject
              << " / workers=" << worker_count << '\n';
    return telemetry::ingestor::run_ingestor(nats_url.c_str(), stream_name.c_str(), subject.c_str(), static_cast<std::size_t>(worker_count));
}