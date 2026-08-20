# Supported Toolchains

| Tool | v1 support statement | Evidence |
|---|---|---|
| CMake | `>= 3.25` | CMake project/presets |
| Ninja | 1.13.2 | CI output |
| vcpkg | tested tool revision + manifest baseline | bootstrap script + `vcpkg.json` |
| Compiler family | GNU / MinGW GCC | The last successful configure reported `The CXX compiler identification is GNU 15.2.0` and `Compiler found: C:/Program Files/mingw64/bin/c++.exe`. |
| Compiler version tested | GNU 15.2.0 | Reported directly in the successful configure output. |
