import asyncio

from cloud_img.jobs import cache_string, get_cache_string


async def test_redis_cache_bg(bg, faker):
    tasks = bg.tasks
    set_task_name = cache_string.name
    get_task_name = get_cache_string.name
    cache_id = faker.word()
    string = faker.word()

    await tasks.queue(set_task_name, cache_id=cache_id, string=string)
    task = await tasks.queue(get_task_name, cache_id=cache_id)
    assert task.result == string

    await tasks.queue(
        set_task_name,
        cache_id=cache_id,
        string=string,
        delay=0.1,
        callback=False)
    await asyncio.sleep(0.3)
    task = await tasks.queue(
        get_task_name, cache_id=cache_id, delay=0.1, callback=False)
    task = await task.done_callback
    assert task.result == string


async def test_redis_cache_fg(bg, user, faker):
    tasks = bg.tasks
    set_task_name = cache_string.name
    get_task_name = get_cache_string.name
    cache_id = faker.word()
    string = faker.word()
    await tasks.queue(
        set_task_name, cache_id=cache_id, string=string, queue=False)
    task = await tasks.queue(get_task_name, cache_id=cache_id, queue=False)
    assert task.result == string
