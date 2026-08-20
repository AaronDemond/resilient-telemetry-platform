---
name: cross-platform-guidelines
description: This skill checks that new code follows cross platform guidelines, including avoiding Windows-only assumptions, keeping platform-specific code behind clear boundaries, and verifying CMake presets and targets.
---

# rules 
Use the guidelines file [docs/cross_platform_guidelines.md](../docs/cross_platform_guidelines.md) to check that new code (the diff between current changes and last commit) follows cross platform guidelines, including avoiding Windows-only assumptions, keeping platform-specific code behind clear boundaries, and verifying CMake presets and targets.

Make sure that all of the following are true:
  - The guidelines are followed in the new code.
  - there is a log entry made to docs/cross_platform_log.md for any new platform-specific code added.

# Determin Code To Analyze
**There are 3 ways the user can specify the code to analyze:**
1. The user can specify a git commit hash to compare against the current changes.
2. the user can specify the most recent commit to compare against the current changes.
3. the user can specify files or specific lines of code to analyze.

# Procedure
1. Determin the code to analyze as specified by the user.
2. Check that the code follows the cross platform guidelines in [docs/cross_platform_guidelines.md](../docs/cross_platform_guidelines.md).
3. If any new platform-specific code is added, the user is asked if they want to allow the new code. If they allow it, there is a log entry made to docs/cross_platform_log.md for the new platform-specific code added. If they do not allow it, There is a log entry made to docs/cross_platform_log.md detailing what code was rejected, and an alternative implementation is suggested that follows the cross platform guidelines.



