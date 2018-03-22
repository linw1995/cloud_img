from cloud_img.models.user import User
from cloud_img.utils import AuthorizationPolicy


async def test_authorization_success(app, db_manager, faker):
    username = faker.name()
    password = faker.password()
    user = await db_manager.create(User, username=username, password=password)

    identity = user.identity

    authorization_policy = AuthorizationPolicy(app=app)

    assert user.id == await authorization_policy.authorized_userid(identity)


async def test_authorization_fail(app, db_manager, faker):
    username = faker.name()
    password = faker.password()
    user = await db_manager.create(User, username=username, password=password)

    identity = user.identity

    await db_manager.delete(user)

    authorization_policy = AuthorizationPolicy(app=app)

    user_id = await authorization_policy.authorized_userid(identity)

    assert user.id != user_id
    assert user_id is None
