# Cross-Platform Guidelines for C++ / CMake

This repository is Windows-first today and should stay Linux-friendly by default. The safest path is to write portable code and portable build logic first, then isolate the small parts that truly need platform-specific handling behind clear abstraction boundaries.

## Practical guidelines

Prefer standard library APIs, standard CMake features, and feature detection over operating-system guesses. Treat Windows and Linux as first-class targets, even if one is currently the primary build path.

Use one of these patterns whenever possible:

- Normalize data at the boundaries, not throughout the codebase.
- Express capabilities with tests, compiler checks, and target properties.
- Keep platform-specific code small, named, and isolated.
- Make defaults portable; specialize only where the platform truly differs.

## Filesystem paths

Use `std::filesystem::path` for path composition, parsing, and rendering. Do not hand-build paths with string concatenation.

```cpp
#include <filesystem>

namespace fs = std::filesystem;

fs::path root = fs::path{"data"};
fs::path config = root / "config" / "telemetry.json";

// Prefer native formatting only at the edge where a string is required.
std::string display = config.string();
```

When accepting paths from users or tools, keep them as `path` objects internally. If you must serialize them, be explicit about the format you need:

- `path.string()` for the local platform format.
- `path.generic_string()` for slash-separated, portable text output.

## Line endings

Do not rely on the host editor or shell to preserve line endings. Store text files with a consistent repository policy and let tools translate only where needed.

Practical rules:

- Keep source files and generated artifacts deterministic across platforms.
- Avoid code that compares raw text with embedded `\r\n` assumptions.
- When reading files, treat newline normalization as an input concern, not a business rule.

If a file format requires specific endings, enforce that format at the serializer or writer boundary rather than in unrelated code.

## Path separators

Never hard-code `/` or `\\` unless you are dealing with a file format that explicitly requires one separator style.

```cpp
#include <filesystem>

std::filesystem::path log_dir = base_dir / "logs";
std::filesystem::path log_file = log_dir / "latest.log";
```

If a protocol or text format needs forward slashes, convert only for that output:

```cpp
std::string manifest_path = log_file.generic_string();
```

## Compiler-specific code

Prefer standard C++ first. If a compiler extension is necessary, isolate it behind a small wrapper and document why the abstraction exists.

```cpp
#if defined(_MSC_VER)
#  define TELEMETRY_FORCE_INLINE __forceinline
#elif defined(__GNUC__) || defined(__clang__)
#  define TELEMETRY_FORCE_INLINE inline __attribute__((always_inline))
#else
#  define TELEMETRY_FORCE_INLINE inline
#endif
```

Keep compiler checks local and intentional:

- Use `_MSC_VER`, `__clang__`, and `__GNUC__` only when the code really depends on compiler behavior.
- Prefer standard feature test macros or CMake feature checks before falling back to compiler branches.
- Do not let compiler-specific code leak into unrelated modules.

## Feature detection

Check for the feature you need, not the platform you expect.

### In C++

```cpp
#if __cpp_lib_filesystem >= 201703L
#include <filesystem>
#else
#error "std::filesystem is required"
#endif
```

### In CMake

```cmake
target_compile_features(telemetry_core PUBLIC cxx_std_20)

include(CheckCXXSourceCompiles)
check_cxx_source_compiles([[
  #include <filesystem>
  int main() {
    std::filesystem::path p{"."};
    return p.empty();
  }
]] HAS_FILESYSTEM)

if(NOT HAS_FILESYSTEM)
  message(FATAL_ERROR "std::filesystem support is required")
endif()
```

Use `target_compile_features`, `target_compile_definitions`, and `target_include_directories` on targets, not globally, so portability stays localized.

## Build presets and toolchains

Keep presets explicit about generator, compiler, and toolchain behavior. A good preset makes the intended environment obvious and reduces accidental host coupling.

```json
{
  "version": 7,
  "configurePresets": [
    {
      "name": "windows-clang",
      "generator": "Ninja",
      "binaryDir": "${sourceDir}/build/windows-clang",
      "cacheVariables": {
        "CMAKE_C_COMPILER": "clang-cl",
        "CMAKE_CXX_COMPILER": "clang-cl",
        "CMAKE_TOOLCHAIN_FILE": "${sourceDir}/vcpkg/scripts/buildsystems/vcpkg.cmake"
      }
    },
    {
      "name": "linux-clang",
      "generator": "Ninja",
      "binaryDir": "${sourceDir}/build/linux-clang",
      "cacheVariables": {
        "CMAKE_C_COMPILER": "clang",
        "CMAKE_CXX_COMPILER": "clang"
      }
    }
  ]
}
```

For toolchains:

- Keep Windows and Linux settings in separate presets when their compilers or ABIs differ.
- Put cross-compilation settings in a toolchain file, not in application code.
- Avoid assuming the current machine’s path layout, shell, or package manager.

## Dependencies

Prefer dependency declarations that work on both platforms:

- Use `find_package()` first when a package is expected to be installed by the environment.
- Use vcpkg or another package manager in a controlled toolchain path when the project owns the dependency set.
- Keep `FetchContent` for a small number of tightly controlled cases, not as the default escape hatch.

```cmake
find_package(fmt CONFIG QUIET)

if(NOT fmt_FOUND)
  message(FATAL_ERROR "fmt must be provided by the active toolchain")
endif()

target_link_libraries(telemetry_core PRIVATE fmt::fmt)
```

If a dependency is platform-specific, hide it behind a wrapper library so the rest of the code does not care which implementation is active.

## Testing

Write tests that prove behavior, not platform assumptions.

- Run the same unit tests on Windows and Linux whenever practical.
- Include path, newline, and case-sensitivity cases where they matter.
- Prefer deterministic temporary directories and test fixtures over hard-coded absolute paths.
- Register tests with CTest so CI can execute the same set everywhere.

```cmake
add_executable(telemetry_tests test_main.cpp path_tests.cpp)
target_link_libraries(telemetry_tests PRIVATE telemetry_core)
add_test(NAME telemetry_tests COMMAND telemetry_tests)
```

For filesystem-heavy tests, use portable expectations:

```cpp
auto tmp = std::filesystem::temp_directory_path() / "telemetry-tests";
std::filesystem::create_directories(tmp);
```

## Logging

Use a small logging abstraction so the application code does not depend on Windows console behavior, Linux syslog behavior, or a specific third-party backend.

```cpp
class Logger {
public:
  virtual ~Logger() = default;
  virtual void info(std::string_view message) = 0;
  virtual void warn(std::string_view message) = 0;
  virtual void error(std::string_view message) = 0;
};
```

Guidelines for log output:

- Emit UTF-8 text consistently.
- Avoid terminal-color assumptions unless the sink advertises support.
- Keep timestamps, severity, and message formatting backend-agnostic.
- Route platform-specific sinks through adapters rather than sprinkling platform branches through business logic.

## Summary

If a change needs platform-specific handling, make that boundary explicit, test it on both platforms, and keep the rest of the repository on portable C++ and portable CMake. That is the easiest way to support Windows now without painting the Linux path into a corner later.