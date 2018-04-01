from cloud_img.models import Image, ImageWithUploadCfg, UploadCfg


async def test_image_count(db_manager, user, user_2):
    assert await Image.count(db_manager=db_manager) == 0
    assert await Image.count(user_id=user.id, db_manager=db_manager) == 0
    assert await Image.count(user_id=user_2.id, db_manager=db_manager) == 0

    await db_manager.create(Image, user=user)

    assert await Image.count(db_manager=db_manager) == 1
    assert await Image.count(user_id=user.id, db_manager=db_manager) == 1
    assert await Image.count(user_id=user_2.id, db_manager=db_manager) == 0


async def test_images_paginate(db_manager, user, user_2):
    for i in range(10):
        await db_manager.create(Image, user=user)
    for i in range(10):
        await db_manager.create(Image, user=user_2)

    images = list(await Image.paginate(db_manager=db_manager))
    assert isinstance(images[0], Image)
    assert len(images) == 15
    assert images[0].id == 20

    images = list(await Image.paginate(db_manager=db_manager, page_no=2))
    assert isinstance(images[0], Image)
    assert len(images) == 5
    assert images[0].id == 5

    images = list(await Image.paginate(
        db_manager=db_manager, page_no=2, page_size=10))
    assert isinstance(images[0], Image)
    assert len(images) == 10
    assert images[0].id == 10

    images = list(await Image.paginate(user_id=user.id, db_manager=db_manager))
    assert isinstance(images[0], Image)
    assert len(images) == 10
    assert images[0].id == 10


async def test_get_upload_cfgs(db_manager, user):
    upload_cfg_a = await db_manager.create(UploadCfg, user=user, name='test_a')
    upload_cfg_b = await db_manager.create(UploadCfg, user=user, name='test_b')
    for i in range(4):
        image = await db_manager.create(Image, user=user)
        if i % 2:
            await db_manager.create(
                ImageWithUploadCfg, upload_cfg=upload_cfg_a, image=image)
        if i % 3:
            await db_manager.create(
                ImageWithUploadCfg, upload_cfg=upload_cfg_b, image=image)

    upload_cfgs = list(await Image.get_upload_cfgs(
        image_id=1, db_manager=db_manager))
    assert len(upload_cfgs) == 0

    upload_cfgs = list(await Image.get_upload_cfgs(
        image_id=2, db_manager=db_manager))
    assert len(upload_cfgs) == 2

    upload_cfgs = list(await Image.get_upload_cfgs(
        image_id=3, db_manager=db_manager))
    assert len(upload_cfgs) == 1
