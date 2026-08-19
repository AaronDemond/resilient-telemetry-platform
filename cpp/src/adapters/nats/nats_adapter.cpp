#include "telemetry/nats/nats_adapter.hpp"

namespace telemetry::adapters::nats {
    const char* adapter_name() noexcept {
        return "nats";
    }
}