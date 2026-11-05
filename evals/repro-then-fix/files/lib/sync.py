from lib.events import dedupe_latest


def sync(raw_events, sink):
    # Events without a timestamp come from the legacy importer and are dropped here.
    events = [e for e in raw_events if "ts" in e]
    for event in dedupe_latest(events):
        sink.write(event)
