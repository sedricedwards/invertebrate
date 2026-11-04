---
type: llm
focus: trace
weight: 1
---

The review identifies the read-modify-write race in charge() (concurrent charges via asyncio.gather on the same account can overdraw / lose updates) as P0 or P1
