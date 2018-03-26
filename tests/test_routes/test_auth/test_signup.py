from datetime import datetime

from cloud_img.models.user import User


async def test_signup_success(aiohttp_client, app, db_manager, sleep, faker):
    username = faker.name()
    password = faker.password()

    client = await aiohttp_client(app)
    resp = await client.post(
        '/signup', json={
            'username': username,
            'password': password,
        })
    assert resp.status == 200
    respBody = await resp.json()
    assert respBody['message'] == 'signup success'

    user = await db_manager.get(User, username=username)

    assert user.validate_password(password)
    sleep(10)
    assert user.created_at < datetime.utcnow()
    assert user.seen_at < datetime.utcnow()


async def test_signup_fail_by_duplicate(aiohttp_client, app, db_manager,
                                        faker):
    username = faker.name()
    password = faker.password()
    await db_manager.create(User, username=username, password=password)

    client = await aiohttp_client(app)
    resp = await client.post(
        '/signup', json={
            'username': username,
            'password': password,
        })
    assert resp.status == 400
    respBody = await resp.json()
    assert respBody['message'].startswith("""signup fail due to """)


async def test_signup_fail_by_params_error(aiohttp_client, app, db_manager,
                                           faker):
    username = faker.name()
    password = faker.password()

    client = await aiohttp_client(app)
    resp = await client.post(
        '/signup', json={
            'name': username,
            'password': password,
        })
    assert resp.status == 400
    respBody = await resp.json()
    assert respBody['message'] == 'paramaters error'
