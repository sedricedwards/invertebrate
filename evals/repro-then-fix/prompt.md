---
tags: [skill-creator]
max_turns: 40
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

invertebrate: review pr.diff (repo is this folder, already has the change applied), save the review to review.md, then fix all and tell me whether the fixes hold

Input files: pr.diff, lib/events.py, lib/sync.py, tests/test_sync.py
