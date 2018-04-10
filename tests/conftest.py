from datetime import datetime, timedelta

import freezegun
from aiohttp_security.api import IDENTITY_KEY
from aioredis import create_redis
from pytest import fixture

from cloud_img import create_app
from cloud_img.constants import MODE
from cloud_img.models import User, create_db, create_db_manager
from cloud_img.utils import build_redis_uri, get_config


@fixture
def sleep():
    freezegun_control = None

    def fake_sleep(seconds):
        nonlocal freezegun_control
        utcnow = datetime.utcnow()
        if freezegun_control is not None:
            freezegun_control.stop()
        freezegun_control = freezegun.freeze_time(
            utcnow + timedelta(seconds=seconds))
        freezegun_control.start()

    yield fake_sleep

    if freezegun_control is not None:
        freezegun_control.stop()


@fixture
def db(app):
    conf = get_config()['db']['mysql']
    db = create_db(app['mode'], conf)
    app['db'] = db
    return db


@fixture
async def redis_client(app):
    conf = get_config()['db']['redis']
    uri = build_redis_uri(conf)
    redis_client = await create_redis(uri)
    yield redis_client
    await redis_client.close()


@fixture
async def db_manager(loop, app, db):
    db_manager = create_db_manager(db)
    app['db_manager'] = db_manager
    yield db_manager
    await db_manager.close()


@fixture
def app():
    app = create_app(mode=MODE.TEST)
    return app


@fixture
async def bg(loop, app):
    from cloud_img.background import bg_manager
    api = bg_manager(app).api()
    await api.start()
    yield api
    await api.close()


@fixture
async def user(db_manager, faker):
    username = faker.name()
    password = faker.password()
    user = await db_manager.create(User, username=username, password=password)
    return user


@fixture
async def user_2(db_manager, faker):
    username = faker.name()
    password = faker.password()
    user = await db_manager.create(User, username=username, password=password)
    return user


@fixture
async def logined_client(aiohttp_client, app, user):
    client = await aiohttp_client(app)
    cookie_name = app[IDENTITY_KEY]._cookie_name
    client.session.cookie_jar.update_cookies({cookie_name: user.identity})
    return client
