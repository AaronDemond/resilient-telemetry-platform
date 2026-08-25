# Cross-platform implementation log

## 2026-08-24 - Windows clang-cl preset verification

- Scope: `tests/CMakeLists.txt` and `tests/toolchain/verify_clang_bootstrap_preset.cmake`.
- Decision: Run the `clang_bootstrap_preset_configures` check only on Windows.
- Reason: The preset intentionally selects the `clang-cl` driver and `x64-windows-static` vcpkg triplet. Linux CI overrides those values for its actual GCC and Clang builds, so reconfiguring the Windows preset inside Linux CTest would test an invalid host/toolchain combination.
- Portable path: Linux CI still configures, builds, generates protobuf bindings, and runs the shared CTest suite with `x64-linux` and native GCC/Clang.

## 2026-08-25 - Static MSVC runtime for Windows clang-cl

- Scope: `CMakePresets.json` and `tests/toolchain/verify_clang_bootstrap_preset.cmake`.
- Decision: Set `CMAKE_MSVC_RUNTIME_LIBRARY` to the static release/debug runtime selected by the `x64-windows-static` vcpkg triplet.
- Decision: Add a clang-cl-only explicit instantiation for Protobuf's `memswap` extern template at the generated-contract boundary.
- Reason: Project and generated Protobuf objects otherwise defaulted to `/MDd`, while static vcpkg dependencies used `/MTd`, causing `LNK2038` runtime-library mismatches during local Windows links. After aligning the CRT, clang-cl 22 decorated Protobuf's `__restrict` pointer template differently from the MSVC-built vcpkg archive, leaving `memswap<16>` unresolved.
- Portable path: The setting only affects compilers targeting the MSVC ABI. Linux CI continues to override the compiler and triplet with native GCC/Clang and `x64-linux`.
