#pragma once

#include <cstddef>

namespace telemetry::ingestor {

int run_ingestor(
    const char* nats_url,
    const char* stream_name,
    const char* subject,
    std::size_t worker_count = 4);

}  // namespace telemetry::ingestor
