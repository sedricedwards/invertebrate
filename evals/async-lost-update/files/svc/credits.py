import logging
from svc.store import KV

log = logging.getLogger(__name__)
store = KV()

async def charge(account: str, amount: int) -> bool:
    try:
        balance = await store.get(f"credits:{account}")
        if balance < amount:
            return False
        await store.set(f"credits:{account}", balance - amount)
        return True
    except Exception:
        pass

async def refund(account: str, amount: int) -> None:
    balance = await store.get(f"credits:{account}")
    await store.set(f"credits:{account}", balance + amount)
