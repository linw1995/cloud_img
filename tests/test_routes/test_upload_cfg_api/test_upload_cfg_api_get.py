from cloud_img.models import UploadCfg


async def test_pagination(db_manager, faker, logined_client, user):
    resp = await logined_client.get('/upload_cfg')
    assert resp.status == 200
    data = await resp.json()
    assert data['total'] == 0
    assert data['upload_cfgs'] == []
    assert data['page_no'] == 1
    assert data['page_size'] == 15

    for i in range(20):
        await db_manager.create(UploadCfg, user=user)

    resp = await logined_client.get('/upload_cfg')
    assert resp.status == 200
    data = await resp.json()
    assert data['total'] == 20
    assert data['upload_cfgs'][0]['id'] == 20
    assert len(data['upload_cfgs']) == 15
    assert data['page_no'] == 1
    assert data['page_size'] == 15

    resp = await logined_client.get('/upload_cfg?page_no=2')
    assert resp.status == 200
    data = await resp.json()
    assert data['total'] == 20
    assert data['upload_cfgs'][0]['id'] == 5
    assert len(data['upload_cfgs']) == 5
    assert data['page_no'] == 2
    assert data['page_size'] == 15

    resp = await logined_client.get('/upload_cfg?page_no=2&page_size=10')
    assert resp.status == 200
    data = await resp.json()
    assert data['total'] == 20
    assert data['upload_cfgs'][0]['id'] == 10
    assert len(data['upload_cfgs']) == 10
    assert data['page_no'] == 2
    assert data['page_size'] == 10
