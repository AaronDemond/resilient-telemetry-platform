#include <chrono>
#include <iostream>

#include "telemetry/core/version.hpp"

int main() {
    constexpr int iterations = 1000000;

    auto start = std::chrono::steady_clock::now();

    const char* result = nullptr;
    for (int i = 0; i < iterations; ++i) {
        result = telemetry::core::version();
    }

    auto end = std::chrono::steady_clock::now();
    auto elapsed = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    std::cout << "Last result: " << result << '\n';
    std::cout << "Time for " << iterations << " calls: " << elapsed.count() << " us\n";

    return 0;
}