from async_lru import alru_cache
from pq import api

from cloud_img.models import ImageWithUploadCfg, UploadCfg


@alru_cache()
async def get_image_data(redis_client, image_id):
    data = await redis_client.hget('image', image_id)
    return data


@alru_cache()
async def get_upload_cfg(mysql_client, upload_cfg_id):
    upload_cfg = await mysql_client.get(UploadCfg, id=upload_cfg_id)
    return upload_cfg


@api.job()
async def upload_img(self, user_id, image_id, upload_cfg_id):
    """
    dispatch upload img job to broker.

    Parameters
    ----------
    user_id : int
        user's id
    image_id : int
        image's id

        also cache it into redis and lru_cache it into memory
    upload_cfg_id : int
        upload_cfg's id

        lru_cache it into memory

    Usages
    ------

        >>> from cloud_img.background import bg_manager
        >>> api = bg_manager().api()
        >>> task = await api.tasks.queue('upload_img', 1, 1, 1, callback=False)
        >>> task_id = task.id
    """
    db_manager = self.backend.db_manager
    redis_client = self.backend.redis_client
    http_client = self.backend.http_client

    image_bytes = await get_image_data(redis_client, image_id)
    upload_cfg = await get_upload_cfg(db_manager, upload_cfg_id)

    rv, _ = await upload_cfg.upload(http_client, image_bytes)

    # TODO: validate rv
    # TODO: handle exception

    await db_manager.create(
        ImageWithUploadCfg,
        image_id=image_id,
        upload_cfg_id=upload_cfg_id,
        **rv)
