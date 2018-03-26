from cloud_img.models import Image, ImageWithUploadCfg, UploadCfg


async def test_get_image(db_manager, faker, logined_client, user):
    resp = await logined_client.get('/image')
    assert resp.status == 200
    data = await resp.json()
    assert data['total'] == 0
    assert data['images'] == []
    assert data['page_no'] == 1
    assert data['page_size'] == 15

    upload_cfg_a = await db_manager.create(UploadCfg, user=user, name='test_a')
    upload_cfg_b = await db_manager.create(UploadCfg, user=user, name='test_b')
    for i in range(100):
        image = await db_manager.create(Image, user=user)
        if i % 2:
            await db_manager.create(
                ImageWithUploadCfg, upload_cfg=upload_cfg_a, image=image)
        if i % 3:
            await db_manager.create(
                ImageWithUploadCfg, upload_cfg=upload_cfg_b, image=image)

    resp = await logined_client.get('/image')
    assert resp.status == 200
    data = await resp.json()
    assert data['total'] == 100
    assert data['images'][0]['id'] == 100
    assert data['page_no'] == 1
    assert data['page_size'] == 15

    resp = await logined_client.get('/image?page_no=2&page_size=10')
    assert resp.status == 200
    data = await resp.json()
    assert data['total'] == 100
    assert data['images'][0]['id'] == 90
    assert data['page_no'] == 2
    assert data['page_size'] == 10
