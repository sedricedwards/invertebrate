---
type: llm
focus: trace
weight: 1
---

The review flags that for a timezone-aware datetime, naturalday/naturaldate compare its date with the local `date.today()` rather than today in the value's timezone, so the result can be off by one day (e.g. 'tomorrow' instead of 'today')
