---
type: llm
focus: trace
weight: 1
---

The review identifies that src/invoice.ts still divides parsePrice's result by 100, so invoice amounts are 100x too small
