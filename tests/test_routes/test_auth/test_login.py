from aiohttp_security.api import IDENTITY_KEY

from cloud_img.models.user import User


async def test_login_success(aiohttp_client, app, db_manager, faker):
    username = faker.name()
    password = faker.password()
    await db_manager.create(User, username=username, password=password)

    client = await aiohttp_client(app)
    resp = await client.post(
        '/login', json={
            'username': username,
            'password': password,
        })
    assert resp.status == 200
    respBody = await resp.json()
    assert respBody['message'] == 'login success'

    assert app[IDENTITY_KEY]._cookie_name in resp.cookies


async def test_login_fail_by_wrong_password(aiohttp_client, app, db_manager,
                                            faker):
    username = faker.name()
    password = faker.password()
    await db_manager.create(User, username=username, password=password)

    client = await aiohttp_client(app)
    resp = await client.post(
        '/login', json={
            'username': username,
            'password': password + '10',
        })
    assert resp.status == 400
    respBody = await resp.json()
    assert respBody['message'] == 'wrong username or password'

    assert app[IDENTITY_KEY]._cookie_name not in resp.cookies


async def test_login_fail_by_not_exist(aiohttp_client, app, db_manager, faker):
    username = faker.name()
    password = faker.password()

    client = await aiohttp_client(app)
    resp = await client.post(
        '/login', json={
            'username': username + '10',
            'password': password,
        })
    assert resp.status == 400
    respBody = await resp.json()
    assert respBody['message'] == 'wrong username or password'

    assert app[IDENTITY_KEY]._cookie_name not in resp.cookies


async def test_login_fail_by_params_error(aiohttp_client, app, db_manager,
                                          faker):
    username = faker.name()
    password = faker.password()

    client = await aiohttp_client(app)
    resp = await client.post(
        '/login', json={
            'name': username,
            'password': password,
        })
    assert resp.status == 400
    respBody = await resp.json()
    assert respBody['message'] == 'paramaters error'

    assert app[IDENTITY_KEY]._cookie_name not in resp.cookies
