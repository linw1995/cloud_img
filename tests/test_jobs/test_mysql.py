from pq import api

from cloud_img.models import User


@api.job()
async def query_user(self, user_id):
    db_manager = self.backend.db_manager
    user = await db_manager.get(User, id=user_id)
    return user.username


async def test_query_user_fg(bg, user):
    tasks = bg.tasks
    tasks.registry.register(query_user)
    task_name = query_user.name

    task = await tasks.queue(task_name, user_id=user.id, queue=False)
    assert task.result == user.username
