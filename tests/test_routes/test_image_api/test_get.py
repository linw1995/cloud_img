from cloud_img.models import Image, ImageWithUploadCfg, UploadCfg


async def test_get_image_pagination(db_manager, faker, logined_client, user):
    resp = await logined_client.get('/image')
    assert resp.status == 200
    data = await resp.json()
    assert data['total'] == 0
    assert data['images'] == []
    assert data['page_no'] == 1
    assert data['page_size'] == 15

    for i in range(20):
        await db_manager.create(Image, user=user)

    resp = await logined_client.get('/image')
    assert resp.status == 200
    data = await resp.json()
    assert data['total'] == 20
    assert data['images'][0]['id'] == 20
    assert len(data['images']) == 15
    assert data['page_no'] == 1
    assert data['page_size'] == 15

    resp = await logined_client.get('/image?page_no=2')
    assert resp.status == 200
    data = await resp.json()
    assert data['total'] == 20
    assert data['images'][0]['id'] == 5
    assert len(data['images']) == 5
    assert data['page_no'] == 2
    assert data['page_size'] == 15

    resp = await logined_client.get('/image?page_no=2&page_size=10')
    assert resp.status == 200
    data = await resp.json()
    assert data['total'] == 20
    assert data['images'][0]['id'] == 10
    assert len(data['images']) == 10
    assert data['page_no'] == 2
    assert data['page_size'] == 10


async def test_get_image_with_multi_sources(db_manager, faker, logined_client,
                                            user):
    upload_cfg_a = await db_manager.create(UploadCfg, user=user, name='test_a')
    upload_cfg_b = await db_manager.create(UploadCfg, user=user, name='test_b')
    for i in range(3):
        image = await db_manager.create(Image, user=user)
        if i % 2:
            await db_manager.create(
                ImageWithUploadCfg, upload_cfg=upload_cfg_a, image=image)
        if i % 3:
            await db_manager.create(
                ImageWithUploadCfg, upload_cfg=upload_cfg_b, image=image)

    resp = await logined_client.get('/image?page_no=1&page_size=10')
    assert resp.status == 200
    data = await resp.json()
    images = data['images']
    first_img = images[-1]
    second_img = images[-2]
    thrid_img = images[-3]
    assert first_img['id'] == 1
    assert len(first_img['sources']) == 0

    assert second_img['id'] == 2
    assert len(second_img['sources']) == 2

    assert thrid_img['id'] == 3
    assert len(thrid_img['sources']) == 1
