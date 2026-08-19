#include "telemetry/postgres/postgres_adapter.hpp"

namespace telemetry::adapters::postgres {
    const char* adapter_name() noexcept {
        return "postgres";
    }
}