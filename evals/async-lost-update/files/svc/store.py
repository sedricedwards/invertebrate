import asyncio

class KV:
    """Async key-value store; every call yields to the event loop (network round-trip)."""
    def __init__(self):
        self._d = {}

    async def get(self, key, default=0):
        await asyncio.sleep(0.001)
        return self._d.get(key, default)

    async def set(self, key, value):
        await asyncio.sleep(0.001)
        self._d[key] = value
