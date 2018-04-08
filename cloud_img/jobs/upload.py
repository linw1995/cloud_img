import asyncio
import time

from pq import api

from ..models import User


@api.job()
def addition(self, a=0, b=0):
    return a + b


@api.job()
async def asynchronous(self, lag=1):
    start = time.time()
    await asyncio.sleep(lag)
    return time.time() - start


@api.job()
async def query_user(self, user_id):
    db_manager = self.backend.db_manager
    user = await db_manager.get(User, id=user_id)
    return user.username


@api.job()
async def cache_string(self, cache_id, string):
    redis_client = self.backend.redis_client
    await redis_client.hset('cache', cache_id, string)


@api.job()
async def get_cache_string(self, cache_id):
    redis_client = self.backend.redis_client
    rv = await redis_client.hget('cache', cache_id)
    # pulsar-queue will serialize,
    # and bytes can't not be serialized by json or msgpack
    return rv.decode('utf-8')
