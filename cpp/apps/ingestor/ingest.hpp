#pragma once

namespace telemetry::ingestor {

int run_ingestor(const char* nats_url, const char* stream_name, const char* subject);

}  // namespace telemetry::ingestor
