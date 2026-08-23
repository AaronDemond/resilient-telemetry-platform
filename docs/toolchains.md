# Supported Toolchains

## Release record

The release record distinguishes the CI runner image from the actual toolchain support proven by command output.

| Field | Value | Evidence / rationale |
|---|---|---|
| CI runner image | `ubuntu-24.04` | Configured by `runs-on: ubuntu-24.04`; this is environment metadata, not compiler support. |
| GCC major version | `15.x` (`g++ 15.2.0`) | Proven by `g++ --version` output captured in the verified local toolchain session. |
| Clang major version | `22.x` (`clang++ 22.1.8`) | Proven by `clang++ --version` output captured in the verified local toolchain session. |
| CMake version | `4.2.1` | Proven by `cmake --version` output captured in the verified local toolchain session. |
| vcpkg tool revision | recorded at CI runtime | The workflow records `git -C "$VCPKG_ROOT" rev-parse HEAD` after bootstrap. This must be captured from the actual runner, not inferred. |
| vcpkg package baseline | `92417abc362ef576257a936cb7e6c222e0c465c3` | Proven by the manifest entry in `vcpkg.json`. |

## Toolchain status

| Tool | Tested configuration | Evidence |
|---|---|---|
| CMake | `>= 3.25` | CMake project and presets |
| Ninja | 1.13.2 | Project generator |
| vcpkg | Manifest mode with the pinned baseline | `vcpkg.json` and CMake presets |
| GCC | `15.x` | `g++ --version` output |
| Clang | `22.x` | `clang++ --version` output |
| Diagnostic configurations | Clang debug + GCC debug + dedicated sanitizer jobs | CI jobs run `cmake --preset debug`, `cmake --preset asan-ubsan`, and `cmake --preset tsan` with explicit toolchain logging |

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

## Rationale for future image changes

A hosted runner image can change independently of the project’s compiler support. If a new image introduces a new compiler and the build fails, the project must:

1. inspect the new diagnostic/failure,
2. determine whether it exposes a real project issue,
3. fix it or deliberately pin a tested compiler version,
4. update this document,
5. keep the rationale in the release record.

The project must not silently weaken warnings just to return CI to green.





