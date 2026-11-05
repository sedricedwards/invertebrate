from lib.sync import sync


class ListSink:
    def __init__(self):
        self.items = []

    def write(self, item):
        self.items.append(item)


def test_sync_drops_untimestamped():
    sink = ListSink()
    sync([{"id": 1}, {"id": 2, "ts": 5}], sink)
    assert [e["id"] for e in sink.items] == [2]
