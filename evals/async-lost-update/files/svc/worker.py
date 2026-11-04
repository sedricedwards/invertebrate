import asyncio
from svc.credits import charge

async def process_batch(jobs):
    results = await asyncio.gather(*(charge(j["account"], j["cost"]) for j in jobs))
    return [j for j, ok in zip(jobs, results) if ok]
