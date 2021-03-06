from aiohttp_security.api import IDENTITY_KEY


async def test_logout_success(aiohttp_client, app, db_manager, faker, user):
    client = await aiohttp_client(app)

    cookie_name = app[IDENTITY_KEY]._cookie_name

    client.session.cookie_jar.update_cookies({cookie_name: user.identity})

    resp = await client.post('/logout')
    assert resp.status == 200
    respBody = await resp.json()
    assert respBody['message'] == 'logout success'

    assert resp.cookies[cookie_name].value == ''


async def test_logout_forbiden(aiohttp_client, app, db_manager, faker):
    client = await aiohttp_client(app)

    resp = await client.post('/logout')
    assert resp.status == 401
