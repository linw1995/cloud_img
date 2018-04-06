import asyncio
import time

from pq import api


@api.job()
def addition(self, a=0, b=0):
    return a + b


@api.job()
async def asynchronous(self, lag=1):
    start = time.time()
    await asyncio.sleep(lag)
    return time.time() - start
