from datetime import datetime, timedelta

import freezegun
from pytest import fixture

from cloud_img import create_app
from cloud_img.constants import MODE
from cloud_img.models import create_db, create_db_manager


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
