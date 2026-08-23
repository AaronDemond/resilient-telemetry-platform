## Summary

<!-- Briefly describe what this PR changes. -->

## Checklist

- [ ] I reviewed [docs/cross_platform_guidelines.md](../docs/cross_platform_guidelines.md) and avoided Windows-only assumptions in shared code.
- [ ] I updated or added tests for any path, file, or platform-sensitive behavior.
- [ ] I kept platform-specific code behind a clear boundary such as an adapter or toolchain file.
- [ ] I verified the affected CMake preset(s) and target(s) still configure and build.
