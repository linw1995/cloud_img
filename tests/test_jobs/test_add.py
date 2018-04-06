import pytest


@pytest.mark.xfail(reason='work on win10, other platform not test yet')
async def test_add_bg(bg):
    tasks = bg.tasks
    task = await tasks.queue('addition', a=1, b=1)
    assert task.result == 2

    task = await tasks.queue('addition', a=1, b=1, delay=0.1, callback=False)
    task = await task.done_callback
    assert task.result == 2


async def test_add_fg(bg):
    tasks = bg.tasks
    task = await tasks.queue('addition', a=1, b=1, queue=False)
    assert task.result == 2
