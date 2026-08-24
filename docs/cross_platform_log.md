# Cross-platform implementation log

## 2026-08-24 - Windows clang-cl preset verification

- Scope: `tests/CMakeLists.txt` and `tests/toolchain/verify_clang_bootstrap_preset.cmake`.
- Decision: Run the `clang_bootstrap_preset_configures` check only on Windows.
- Reason: The preset intentionally selects the `clang-cl` driver and `x64-windows-static` vcpkg triplet. Linux CI overrides those values for its actual GCC and Clang builds, so reconfiguring the Windows preset inside Linux CTest would test an invalid host/toolchain combination.
- Portable path: Linux CI still configures, builds, generates protobuf bindings, and runs the shared CTest suite with `x64-linux` and native GCC/Clang.
