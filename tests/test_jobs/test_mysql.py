import pytest

from cloud_img.jobs import query_user


@pytest.mark.xfail(reason='work on win10, other platform not test yet')
async def test_query_user_bg(bg, user):
    tasks = bg.tasks
    task_name = query_user.name

    task = await tasks.queue(task_name, user_id=user.id)
    assert task.result == user.username

    task = await tasks.queue(
        task_name, user_id=user.id, delay=0.1, callback=False)
    task = await task.done_callback
    assert task.result == user.username


async def test_query_user_fg(bg, user):
    tasks = bg.tasks
    task_name = query_user.name

    task = await tasks.queue(task_name, user_id=user.id, queue=False)
    assert task.result == user.username
