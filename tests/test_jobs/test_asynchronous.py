import pytest


@pytest.mark.xfail(reason='work on win10, other platform not test yet')
async def test_asynchronous_bg(bg):
    tasks = bg.tasks
    task = await tasks.queue('asynchronous', lag=1)
    assert abs(task.result - 1) < 0.05

    task = await tasks.queue('asynchronous', lag=1, delay=0.1, callback=False)
    task = await task.done_callback
    assert abs(task.result - 1) < 0.05


async def test_asynchronous_fg(bg):
    tasks = bg.tasks
    task = await tasks.queue('asynchronous', lag=1, queue=False)
    assert abs(task.result - 1) < 0.05
