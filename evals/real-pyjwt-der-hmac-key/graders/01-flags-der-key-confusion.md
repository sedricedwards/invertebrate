---
type: llm
focus: trace
weight: 1
---

The review flags that after the change a DER-encoded public key or x509 certificate is accepted as an HMAC secret by HMACAlgorithm.prepare_key, so an attacker who knows the public key can forge HS256/HMAC-signed tokens (algorithm confusion)
