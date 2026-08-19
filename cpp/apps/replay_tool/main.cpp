#include <cstdio>

#include "telemetry/core/version.hpp"

int main() {
    std::puts(telemetry::core::version());
    return 0;
}