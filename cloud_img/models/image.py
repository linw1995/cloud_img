from datetime import datetime

import peewee


__all__ = ('Image', )


class Image(peewee.Model):
    from .user import User
    created_at = peewee.DateTimeField(default=datetime.utcnow)
    seen_at = peewee.DateTimeField(default=datetime.utcnow)
    description = peewee.CharField(max_length=255)

    user = peewee.ForeignKeyField(User, related_name='images')

    class Meta:
        from . import db_proxy
        database = db_proxy
        db_table = 'image'
