import functools
import logging
import logging.handlers
import pathlib
import re
import time

import yaml
from aiohttp import web
from aiohttp_security import AbstractAuthorizationPolicy, authorized_userid
from lxml import etree

from .constants import GLOBAL, MODE


__all__ = ('get_config', 'AuthorizationPolicy', 'config_setup')
_config = []
_mode = None


def get_config():
    """
    get different config depends on app's mode.
    """
    global _config
    assert _config is not None, "use config_setup(app) first."
    conf = _config.copy()
    if _mode is not None:  # pragma: no cover
        conf = conf[_mode]
    conf[GLOBAL] = _config[GLOBAL]
    return conf


def config_setup(app):
    global _config, _mode
    confPath = pathlib.Path('.') / 'conf.yaml'
    _config = yaml.load(confPath.read_text('utf-8'))
    _mode = app['mode']


def log_setup(app):
    """
    setup the log handler.

    + `StreamHandler` logging into console.
    + `TimedRotatingFileHandler` logging into timed rotating file.
    """
    mode = app['mode']
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        '%Y-%m-%dT%H:%M:%S%z')

    logger = logging.getLogger()
    logger.setLevel(logging.NOTSET)

    if mode != MODE.TEST:  # pragma: no cover
        std_handler = logging.StreamHandler()
        std_handler.setFormatter(formatter)

        file_handler = logging.handlers.TimedRotatingFileHandler(
            f'{mode}.log', when='h', encoding='utf8', backupCount=5, utc=True)
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
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


def login_required(fn):  # pragma: no cover
    """Decorator that restrict access only for authorized users.

    User is considered authorized if authorized_userid
    returns some value.

    import from aiohttp_security.api
    """

    @functools.wraps(fn)
    async def wrapped(*args, **kwargs):
        request = args[-1]
        if not isinstance(request, web.BaseRequest):
            msg = ("Incorrect decorator usage. "
                   "Expecting `def handler(request)` "
                   "or `def handler(self, request)`.")
            raise RuntimeError(msg)

        userid = await authorized_userid(request)
        if userid is None:
            raise web.HTTPUnauthorized

        request.user_id = userid

        ret = await fn(*args, **kwargs)
        return ret

    return wrapped


KEY_INDEX_PATTERN = re.compile(r'((?P<key>[^\s\.\[\]]+)'
                               r'((?P<left>\[)(?P<index>\d+)(?(left)\]))?)+?')


def query_json(resource, path):
    """
    parse query_path to load the value through the path from json data.

    TODO: unescape the path
    """
    error_msg = f'query json path {path!r} is invalid.'
    try:
        for match in KEY_INDEX_PATTERN.finditer(path):
            group = match.groupdict()
            key = group['key']
            assert isinstance(resource, dict)
            resource = resource[key]
            if group['index']:
                index = int(group['index'])
                assert isinstance(resource, list)
                assert index >= 1, ' the index should start at 1.'
                assert index < len(resource) + 1, ' index out of range.'
                resource = resource[index - 1]

        rv_type = type(resource)
        assert issubclass(rv_type, (str, int, float)), \
            f'result type must be str, int or float, but get {rv_type}'
        return resource
    except AssertionError as err:
        raise ValueError(f'{error_msg}{err}')
    except KeyError as key:
        raise ValueError(f'{error_msg} key {key} no exists')


def query_xml(resource, path):
    """
    parse query_path to load the value through the path from xml data.

    TODO: unescape the path
    """
    error_msg = f'query xml path {path!r} is invalid.'
    try:
        for match in KEY_INDEX_PATTERN.finditer(path):
            group = match.groupdict()
            key = group['key']
            if isinstance(resource, etree._Element):
                if resource.tag != key:
                    raise KeyError(key)
                assert group['index'] is None
                resource = resource.getchildren()
            elif isinstance(resource, list):
                resource = [elem for elem in resource if elem.tag == key]
                if len(resource) == 0:
                    raise KeyError(key)
                if group['index']:
                    index = int(group['index'])
                    assert index >= 1, ' the index should start at 1.'
                    assert index < len(resource) + 1, ' index out of range.'
                    resource = resource[index - 1]
                else:
                    resource = resource[0]
            else:
                raise AssertionError(' not supposed to happen.')
        assert len(resource) == 0, ' it must be the deepest element.'
        return resource.text
    except AssertionError as err:
        raise ValueError(f'{error_msg}{err}')
    except KeyError as key:
        raise ValueError(f'{error_msg} key {key} no exists')


def query_regex(resource, raw_pattern):
    """
    use regex to load the value from raw data.
    """
    error_msg = f'query regex pattern {raw_pattern!r} is invalid.'
    try:
        pattern = re.compile(raw_pattern)
        match = pattern.search(resource)
        assert match is not None, ' pattern should match something.'
        return match.group(1)
    except AssertionError as err:
        raise ValueError(f'{error_msg}{err}')
    except re.error:
        raise ValueError(f'{error_msg}')


def datetime2unix(dt):
    tt = dt.timetuple()
    return time.mktime(tt)
