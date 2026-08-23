---
description: "Append the latest user prompt and the visible assistant output for this turn to output.md"
name: "writeoutput"
argument-hint: "Log the current prompt and output"
---
Append a new entry to the repo-root file

the file is located at C:\Users\19024\Documents\ObsidianVaults\Programming\career\Lockheed Martin\Projects\resilient telemetry platform\output.md
 (located at:  rewriting or truncating any existing content.

Do NOT delete or modify any content in the file that is not part of the latest user prompt and the visible assistant output for this turn.

Add a human readable (Like December 21st, 2026, 4:30 AM) timestamp to the entry.

User the following as a formatting guide

```markdown
# Timestamp: (Time stamp goes here)

# Prompt
<the most recent user prompt that triggered this command>

# Output
<all visible assistant output generated for this turn, up to the moment this prompt is invoked>

# Summary
## Prompt Summary
(A summary of the users prompt goes here)
## Response Summary
(A Summary of the assistant response goes here)
```

(add a blank line after the last line of the output to separate it from the next entry)

```

Rules:
- Preserve everything already in [output.md](../../output.md).
- Append only; do not delete or rewrite previous entries.
- Use the exact latest user prompt text immediately before this command.
- Include every visible assistant response generated for that prompt, including intermediate updates or commentary that were shown to the user in chat before this prompt was invoked.
- Separate appended entries with a blank line.
- Do not add commentary outside the required markdown structure.
- The target file is the repository root [output.md](../../output.md).
