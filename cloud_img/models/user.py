from datetime import datetime

import jwt
import peewee
from werkzeug.security import check_password_hash, generate_password_hash

from ..constants import GLOBAL, JWT_KEY_CONFIG, JWT_KEY_DEFAULT
from ..utils import Config


__all__ = ('User', )


class User(peewee.Model):
    username = peewee.CharField(max_length=255, null=False, unique=True)
    password_hash = peewee.CharField(max_length=255, null=False)
    created_at = peewee.DateTimeField(default=datetime.utcnow)
    seen_at = peewee.DateTimeField(default=datetime.utcnow)

    class Meta:
        from . import db_proxy
        database = db_proxy
        db_table = 'user'

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def password(self):
        raise NotImplementedError(
            'should save password_hash instead of password')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    @property
    def identity(self):
        """user security identity"""
        # TODO: better way to import the config
        # config.get(JWT_KEY_CONFIG)
        config = Config()
        key = config.get(GLOBAL, {}).get(JWT_KEY_CONFIG, JWT_KEY_DEFAULT)
        payload = {'user_id': self.id}
        jwt_bytes = jwt.encode(payload=payload, key=key, algorithm='HS256')
        return jwt_bytes.decode('utf8')

    @classmethod
    def decode_identity(self, identity):
        """
        decode identity.

        return the `user_id` by the identity
        or 'None' if identity decode fail.
        """
        config = Config()
        key = config.get(GLOBAL, {}).get(JWT_KEY_CONFIG, JWT_KEY_DEFAULT)
        jwt_bytes = identity.encode('utf8')
        try:
            payload = jwt.decode(jwt=jwt_bytes, key=key, algorithms='HS256')
            return payload.get('user_id')
        except jwt.DecodeError:
            return None
