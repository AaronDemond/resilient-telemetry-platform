#include "telemetry/core/version.hpp"

int main() {
    
    // Retrieve the version string from the telemetry::core namespace
    const char* version = telemetry::core::version();

    // Check if the version string is not null and not empty
    return (version != nullptr && version[0] != '\0') ? 0 : 1;
}