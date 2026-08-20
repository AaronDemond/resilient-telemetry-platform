#include <string_view>

#include "telemetry/postgres/postgres_adapter.hpp"

int main() {
    return std::string_view(telemetry::adapters::postgres::adapter_name()) == "postgres"
        ? 0
        : 1;
}