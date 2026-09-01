#include <drogon/drogon.h>

#include <filesystem>
#include <iostream>
#include <string>

#include "telemetry/core/version.hpp"
#include "units_api_v1.h"

namespace {

std::filesystem::path find_config_file(const std::filesystem::path& executable_path) {
    const std::filesystem::path current_dir = std::filesystem::current_path();
    std::vector<std::filesystem::path> search_roots;

    if (!executable_path.empty()) {
        search_roots.push_back(executable_path.parent_path());
    }
    search_roots.push_back(current_dir);

    for (const auto& root : search_roots) {
        const auto candidate = root / "config.json";
        if (std::filesystem::exists(candidate) && std::filesystem::is_regular_file(candidate)) {
            return candidate;
        }
    }

    std::filesystem::path probe = executable_path.empty() ? current_dir : executable_path.parent_path();
    for (int level = 0; level < 8; ++level) {
        const auto candidate = probe / "config.json";
        if (std::filesystem::exists(candidate) && std::filesystem::is_regular_file(candidate)) {
            return candidate;
        }

        const auto parent = probe.parent_path();
        if (parent == probe) {
            break;
        }
        probe = parent;
    }

    return current_dir / "config.json";
}

}  // namespace

int main(int argc, char** argv) {
    // Drogon auto-registers controllers declared with METHOD_LIST_BEGIN / METHOD_LIST_END.
    // Explicit registerController(...::instance()) is invalid for this controller pattern.
    const std::filesystem::path executable_path = argc > 0 ? std::filesystem::absolute(argv[0]) : std::filesystem::path{};
    const std::filesystem::path config_path = find_config_file(executable_path);

    if (!std::filesystem::exists(config_path) || !std::filesystem::is_regular_file(config_path)) {
        std::cerr << "Could not find config.json. Searched from: " << executable_path.parent_path().string()
                  << " and " << std::filesystem::current_path().string() << std::endl;
    } else {
        std::cout << "Using config: " << config_path.string() << std::endl;
    }

    drogon::app().setLogLevel(trantor::Logger::LogLevel::kWarn);
    drogon::app().loadConfigFile(config_path.string());
    drogon::app().run();
    return 0;
}