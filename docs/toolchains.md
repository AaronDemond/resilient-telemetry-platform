# Supported Toolchains

| Tool | Supported configuration | Evidence |
|---|---|---|
| CMake | `>= 3.25` | CMake project and presets |
| Ninja | 1.13.2 | Project generator |
| vcpkg | Manifest mode with the pinned baseline | `vcpkg.json` and CMake presets |
| Compiler family | Clang / LLVM (`clang++`) | Clang-only CMake preset family |
| Diagnostic configurations | None published | The active `clang++` toolchain fails the ASan capability check; TSan and coverage remain unpublished pending their own configure-time capability checks. |

## Standard Workflow

Use the Clang presets from the repository root:

```powershell
cmake --preset clang-bootstrap
cmake --build --preset clang-bootstrap
ctest --preset clang-bootstrap --output-on-failure
```





