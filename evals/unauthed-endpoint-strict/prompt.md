---
tags: [skill-creator]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

invertebrate: Review this PR (diff in pr.diff, repo checked out in cwd, it has a .greptile config). Is it safe to merge? Write the review to review.md.

Input files: pr.diff, app/views.py, app/auth.py, app/audit.py, app/db.py, .greptile/config.json, .greptile/rules.md
