#include <string_view>

#include "telemetry/nats/nats_adapter.hpp"

int main() {
    return std::string_view(telemetry::adapters::nats::adapter_name()) == "nats"
        ? 0
        : 1;
}