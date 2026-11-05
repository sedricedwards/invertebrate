---
type: llm
focus: trace
weight: 1
---

The review flags that removing the 'if order.charged: return' guard lets a retried payment webhook capture the payment twice (double charge)
