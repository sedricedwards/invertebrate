# Simplify setKey

Go back to the `forEach` loop in `setKey` and drop the per-prototype special cases; the `{}.__proto__` check already covers it.
