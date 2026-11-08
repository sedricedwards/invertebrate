---
type: llm
focus: trace
weight: 1
---

The review flags that with a custom `choice` function (e.g. `min` or `max`), popitem() on an empty RRCache raises that function's own exception (such as ValueError) instead of KeyError
