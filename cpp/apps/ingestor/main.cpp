#include <cstdlib>

#include "ingest.hpp"

namespace {

constexpr const char* kDefaultNatsUrl = "nats://127.0.0.1:14222";
constexpr const char* kDefaultStreamName = "TELEMETRY_TEST_STREAM";
constexpr const char* kDefaultSubject = "telemetry.test.ingestor";

const char* env_or_default(const char* name, const char* fallback) noexcept {
    if (const char* value = std::getenv(name); value != nullptr && value[0] != '\0') {
        return value;
    }

    return fallback;
}

}  // namespace

int main() {
    const char* nats_url = env_or_default("TELEMETRY_NATS_URL", kDefaultNatsUrl);
    const char* stream_name = env_or_default("TELEMETRY_TEST_STREAM", kDefaultStreamName);
    const char* subject = env_or_default("TELEMETRY_TEST_SUBJECT", kDefaultSubject);

    return telemetry::ingestor::run_ingestor(nats_url, stream_name, subject);
}