from datetime import datetime, timedelta

import pytest

from cloud_img.models.user import User


one_second = timedelta(seconds=1)


async def test_user_create_and_save(db_manager, faker):
    username = faker.name()
    password = faker.password()
    user = await db_manager.create(User, username=username, password=password)

    assert user.id is not None
    with pytest.raises(NotImplementedError):
        assert user.password == password
    assert user.password_hash is not None
    assert user.validate_password(password)
    assert abs(user.created_at - datetime.utcnow()) < one_second
    assert abs(user.seen_at - datetime.utcnow()) < one_second

    user_from_db = await db_manager.get(User, username=username)

    assert user_from_db.id is not None
    assert user_from_db.username == username
    assert user_from_db.validate_password(password)
    assert abs(user_from_db.created_at - user.created_at) < one_second
    assert abs(user_from_db.seen_at - user.seen_at) < one_second


async def test_user_edit_and_save(db_manager, faker):
    username = faker.name()
    password = faker.password()

    user = await db_manager.create(User, username=username, password=password)

    assert user.id is not None

    username = faker.name()
    password = faker.password()

    assert user.username != username
    assert not user.validate_password(password)

    user.username = username
    user.password = password

    await db_manager.update(user)

    user_from_db = await db_manager.get(User, username=username)

    assert user_from_db.id == user.id
    assert user_from_db.username == username
    assert user_from_db.validate_password(password)
    assert abs(user_from_db.created_at - user.created_at) < one_second
    assert abs(user_from_db.seen_at - user.seen_at) < one_second


async def test_user_identity(db_manager, faker):
    username = faker.name()
    password = faker.password()
    user = await db_manager.create(User, username=username, password=password)

    identity = user.identity

    user_id = User.decode_identity(identity)

    assert user_id == user.id

    user_id = User.decode_identity('')

    assert user_id is None
