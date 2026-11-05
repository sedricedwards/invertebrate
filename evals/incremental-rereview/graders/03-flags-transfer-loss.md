---
type: llm
focus: trace
weight: 1
---

The review flags that transfer() debits src before dst.credit() can raise Frozen, so money is lost when dst is frozen, as P0 or P1
