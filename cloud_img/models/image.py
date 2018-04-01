from datetime import datetime

import peewee

from ..utils import datetime2unix


__all__ = ('Image', )


class Image(peewee.Model):
    from .user import User
    created_at = peewee.DateTimeField(default=datetime.utcnow)
    seen_at = peewee.DateTimeField(default=datetime.utcnow)
    description = peewee.CharField(max_length=255, default='')

    user = peewee.ForeignKeyField(User, related_name='images')

    class Meta:
        from . import db_proxy
        database = db_proxy
        db_table = 'image'

    def toJSON(self):
        return {
            'id': self.id,
            'created_at': datetime2unix(self.created_at),
            'seen_at': datetime2unix(self.seen_at),
            'description': self.description,
        }

    @classmethod
    async def count(cls, user_id=None, *, db_manager):
        sql = cls.select()
        if user_id is not None:
            sql = sql.where(cls.user_id == user_id)
        return await db_manager.count(sql)

    @classmethod
    async def paginate(cls,
                       user_id=None,
                       page_no=1,
                       page_size=15,
                       *,
                       db_manager):
        sql = cls.select()
        if user_id is not None:
            sql = sql.where(cls.user_id == user_id)
        sql = sql \
            .order_by(cls.id.desc()) \
            .paginate(page_no, page_size)
        return await db_manager.execute(sql)

    @classmethod
    async def get_upload_cfgs(cls, image_id, *, db_manager):
        from .upload_cfg import ImageWithUploadCfg
        sql = ImageWithUploadCfg \
            .select() \
            .where(ImageWithUploadCfg.image_id == image_id)
        return await db_manager.execute(sql)
