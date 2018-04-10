from pathlib import Path

from aiohttp import web

from cloud_img.jobs import upload_img
from cloud_img.models import Image, ImageWithUploadCfg, UploadCfg


async def test_upload_img_fg(bg, redis_client, db_manager, user,
                             aiohttp_server):
    tasks = bg.tasks
    task_name = upload_img.name

    image_bytes = Path('tests/assets/python.png').read_bytes()
    image = await db_manager.create(Image, user=user)
    await redis_client.hset('image', image.id, image_bytes)

    async def handler(request):
        data = await request.post()
        files = data.getall('file')
        assert len(files) == 1
        assert files[0].file.read() == image_bytes
        return web.json_response({'id': 1})

    app = web.Application()
    app.router.add_post('/', handler)
    server = await aiohttp_server(app)

    upload_cfg = await db_manager.create(
        UploadCfg,
        user=user,
        request_url=server.make_url('/'),
        request_formdata={'file': '$input$'},
        image_url_querystr='https://example.com/$json:id$')

    task = await tasks.queue(
        task_name,
        user_id=user.id,
        image_id=image.id,
        upload_cfg_id=upload_cfg.id,
        queue=False)
    assert task.status_string == 'SUCCESS'

    img_with_upload_cfg = await db_manager.get(
        ImageWithUploadCfg, upload_cfg_id=upload_cfg.id)
    assert img_with_upload_cfg.image_id == image.id
    assert img_with_upload_cfg.image_url == 'https://example.com/1'


async def test_upload_img_fg_to__sm_dot_ms(bg, redis_client, db_manager, user,
                                           session):
    tasks = bg.tasks
    task_name = upload_img.name

    image_bytes = Path('tests/assets/python.png').read_bytes()
    image = await db_manager.create(Image, user=user)
    await redis_client.hset('image', image.id, image_bytes)

    upload_cfg = await db_manager.create(
        UploadCfg,
        user=user,
        request_url='https://sm.ms/api/upload',
        request_formdata={'smfile': '$input$'},
        request_querystring={
            'ssl': 'true',
            'format': 'json',
        },
        image_url_querystr='$json:data.url$',
        delete_url_querystr='$json:data.delete$')

    task = await tasks.queue(
        task_name,
        user_id=user.id,
        image_id=image.id,
        upload_cfg_id=upload_cfg.id,
        queue=False)
    assert task.status_string == 'SUCCESS'

    img_with_upload_cfg = await db_manager.get(
        ImageWithUploadCfg, upload_cfg_id=upload_cfg.id)
    assert img_with_upload_cfg.image_id == image.id
    assert img_with_upload_cfg.image_url != ''
    assert img_with_upload_cfg.delete_url != ''
    assert img_with_upload_cfg.thumbnail_url == ''

    async with session.get(img_with_upload_cfg.image_url) as resp:
        assert resp.status == 200

    async with session.get(img_with_upload_cfg.delete_url) as resp:
        assert resp.status == 200
