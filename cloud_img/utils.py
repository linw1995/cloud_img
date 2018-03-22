import logging
import logging.handlers
import pathlib

import yaml
from aiohttp_security import AbstractAuthorizationPolicy

from .constants import MODE


__all__ = ('get_config', 'AuthorizationPolicy', 'config_setup', 'Config')
_config = None


def get_config(app):
    """
    get different config depends on app's mode.
    """
    mode = app['mode']
    conf = app['config']
    if mode is not None:  # pragma: no cover
        conf = conf[mode]
    return conf


def Config():
    """
    use `Config()` for global config sharing.

    TODO: make it immutable
    """
    global _config
    assert _config is not None, "Cannot use uninitialized Config."
    return _config


def config_setup(app):
    global _config
    confPath = pathlib.Path('.') / 'conf.yaml'
    _config = yaml.load(confPath.read_text('utf-8'))
    app['config'] = _config


def log_setup(app):
    """
    setup the log handler.

    + `StreamHandler` logging into console.
    + `TimedRotatingFileHandler` logging into timed rotating file.
    """
    mode = app['mode']
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    file_handler = logging.handlers.TimedRotatingFileHandler(
        f'{mode}.log', when='h', encoding='utf8', backupCount=5, utc=True)
    file_handler.setFormatter(formatter)

    std_handler = logging.StreamHandler()
    std_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.NOTSET)

    # remove existing handler
    for handler in logger.handlers:
        handler.close()
        logger.removeHandler(handler)

    logger.addHandler(file_handler)
    if mode != MODE.TEST:
        logger.addHandler(std_handler)

    logger.info('logging handlers %r', logger.handlers)

    logger.setLevel(logging.INFO)
    if mode in (MODE.DEBUG, MODE.TEST):  # pragma: no cover
        logger.setLevel(logging.DEBUG)


class AuthorizationPolicy(AbstractAuthorizationPolicy):
    """
    authorization policy for the `aiohttp_security` extension.
    """

    def __init__(self, *, app):
        self.app = app

    async def permits(self, identity, permission, context=None):
        """Check user permissions.

        Return True if the identity is allowed the permission in the
        current context, else return False.
        """
        raise NotImplementedError()

    async def authorized_userid(self, identity):
        """Retrieve authorized user id.

        Return the user_id of the user identified by the identity
        or 'None' if no user exists related to the identity.
        """
        from .models import User
        user_id = User.decode_identity(identity)
        if user_id:
            db_manager = self.app['db_manager']
            try:
                await db_manager.get(User, id=user_id)
            except User.DoesNotExist:
                return None
            return user_id
