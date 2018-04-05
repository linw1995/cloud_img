import logging

from aiohttp import web

from ..models import UploadCfg
from ..utils import login_required


logger = logging.getLogger(__name__)
__all__ = ('UploadCfgApi', )


class UploadCfgApi:
    @login_required
    async def get(request):
        query = request.query
        logger.debug('user_id: %d, query: %r', request.user_id, query)
        page_no = query.get('page_no', 1)
        page_no = int(page_no)
        page_no = page_no if page_no > 0 else 1
        page_size = query.get('page_size', 15)
        page_size = int(page_size)
        page_size = page_size if page_size < 15 else 15

        user_id = request.user_id
        db_manager = request.app['db_manager']
        # get total count of user's upload config
        total = await UploadCfg.count(user_id=user_id, db_manager=db_manager)
        # paginate the upload config table
        upload_cfgs = await UploadCfg.paginate(
            user_id=user_id,
            page_no=page_no,
            page_size=page_size,
            db_manager=db_manager)

        upload_cfgs = [upload_cfg.toJSON() for upload_cfg in upload_cfgs]

        logger.debug('upload_cfgs count: %d, total: %d', len(upload_cfgs),
                     total)
        return web.json_response({
            'upload_cfgs': upload_cfgs,
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
