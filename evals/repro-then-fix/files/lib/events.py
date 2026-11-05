def dedupe_latest(events):
    """Return one event per id, keeping the most recent (highest ts)."""
    seen = {}
    for event in sorted(events, key=lambda e: e["ts"]):
        seen.setdefault(event["id"], event)
    return list(seen.values())
