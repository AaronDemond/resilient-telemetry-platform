# Supported Toolchains

| Tool | v1 support statement | Evidence |
|---|---|---|
| CMake | `>= 3.25` | CMake project/presets |
| Ninja | 1.13.2 | CI output |
| vcpkg | tested tool revision + manifest baseline | bootstrap script + `vcpkg.json` |
| Compiler family | Clang / LLVM toolset (`clang-cl`) | The bootstrap preset is Clang-only and uses the Windows MSVC ABI triplet. |
| Compiler version tested | Not yet recorded | Capture this after the first successful Clang bootstrap configure. |# Supported Toolchains


