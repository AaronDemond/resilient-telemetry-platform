---
name: cross-platform-guidelines
description: This skill checks that new code follows cross platform guidelines, including avoiding Windows-only assumptions, keeping platform-specific code behind clear boundaries, and verifying CMake presets and targets.
---

# rules 
Use the guidelines file [docs/cross_platform_guidelines.md](../docs/cross_platform_guidelines.md) to check that new code (the diff between current changes and last commit) follows cross platform guidelines, including avoiding Windows-only assumptions, keeping platform-specific code behind clear boundaries, and verifying CMake presets and targets.

Make sure that all of the following are true:
  - The guidelines are followed in the new code.
  - there is a log entry made to docs/cross_platform_log.md for any new platform-specific code added.


# Procedure
1. Check the diff between the current changes and the last commit, or a specific git commit hash, if provided.
2. For any new code, check that it follows the cross platform guidelines in [docs/cross_platform_guidelines.md](../docs/cross_platform_guidelines.md).
3. If any new platform-specific code is added, the user is asked if they want to allow the new code. If they allow it, there is a log entry made to docs/cross_platform_log.md for the new platform-specific code added. If they do not allow it, There is a log entry made to docs/cross_platform_log.md detailing what code was rejected, and an alternative implementation is suggested that follows the cross platform guidelines.



