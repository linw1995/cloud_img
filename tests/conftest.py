from datetime import datetime, timedelta

import freezegun
from aiohttp_security.api import IDENTITY_KEY
from pytest import fixture

from cloud_img import create_app
from cloud_img.constants import MODE
from cloud_img.models import User, create_db, create_db_manager


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
    return create_db(app)


@fixture
async def db_manager(loop, app, db):
    db_manager = create_db_manager(app, db)
    yield db_manager
    await db_manager.close()


@fixture
def app():
    app = create_app(mode=MODE.TEST)
    return app


@fixture
async def user(db_manager, faker):
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
