# Supported Toolchains

| Tool | Supported configuration | Evidence |
|---|---|---|
| CMake | `>= 3.25` | CMake project and presets |
| Ninja | 1.13.2 | Project generator |
| vcpkg | Manifest mode with the pinned baseline | `vcpkg.json` and CMake presets |
| Compiler family | Clang / LLVM (`clang++`) | Clang-only CMake preset family |
| Diagnostic configurations | None published | The active `clang++` toolchain fails the ASan capability check; TSan and coverage remain unpublished pending their own configure-time capability checks. |

## Standard Workflow

Use the Debug preset from the repository root:

```powershell
cmake --preset debug
cmake --build --preset debug
ctest --preset debug --output-on-failure
```

For CI, enable warnings as errors explicitly:

```powershell
cmake --preset debug -DTELEMETRY_WARNINGS_AS_ERRORS=ON
```





