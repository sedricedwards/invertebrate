# Merge the two eviction loops in Cache.__setitem__

One eviction loop instead of two near-identical branches. No behavior change intended.
