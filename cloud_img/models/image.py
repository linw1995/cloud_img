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
