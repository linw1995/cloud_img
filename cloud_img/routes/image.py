from aiohttp import web

from ..models import Image, ImageWithUploadCfg
from ..utils import login_required


__all__ = ('ImageApi', )


class ImageApi:
    @login_required
    async def get(request):
        query = request.query
        page_no = query.get('page_no', 1)
        page_no = int(page_no)
        page_no = page_no if page_no > 0 else 1
        page_size = query.get('page_size', 15)
        page_size = int(page_size)
        page_size = page_size if page_size < 15 else 15

        user_id = request.user_id

        db_manager = request.app['db_manager']
        sql = Image\
            .select() \
            .where(Image.user_id == user_id)
        total = await db_manager.count(sql)

        sql = Image\
            .select() \
            .where(Image.user_id == user_id) \
            .order_by(Image.id.desc()) \
            .paginate(page_no, page_size)
        images = await db_manager.execute(sql)

        images = [image.toJSON() for image in images]

        for image in images:
            sql = ImageWithUploadCfg \
                .select() \
                .where(ImageWithUploadCfg.image_id == image['id'])
            image_with_upload_cfg = await db_manager.execute(sql)
            image['sources'] = [v.toJSON() for v in image_with_upload_cfg]

        return web.json_response({
            'images': images,
            'page_no': page_no,
            'page_size': page_size,
            'total': total,
        })

    async def post(request):
        raise NotImplementedError()

    async def delete(request):
        raise NotImplementedError()

    async def put(request):
        raise NotImplementedError()
