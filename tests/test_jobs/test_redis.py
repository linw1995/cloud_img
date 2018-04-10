from pq import api


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


async def test_redis_cache_fg(bg, user, faker):
    tasks = bg.tasks
    tasks.registry.register(cache_string)
    tasks.registry.register(get_cache_string)

    set_task_name = cache_string.name
    get_task_name = get_cache_string.name
    cache_id = faker.word()
    string = faker.word()

    await tasks.queue(
        set_task_name, cache_id=cache_id, string=string, queue=False)
    task = await tasks.queue(get_task_name, cache_id=cache_id, queue=False)
    assert task.result == string
