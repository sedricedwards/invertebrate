---
type: llm
focus: trace
weight: 1
---

The review flags src/invoice.ts (calls formatMoney, re-exported from src/index.ts as money.format) as broken because the currency argument is missing
