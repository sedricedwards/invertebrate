---
type: llm
focus: trace
weight: 1
---

The review identifies that src/checkout.ts passes the now-dollar value to createCharge, which expects integer cents (wrong charge amount or thrown error)
