import logging
import logging.handlers
import pathlib
import re

import yaml
from aiohttp_security import AbstractAuthorizationPolicy
from lxml import etree

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
    if mode != MODE.TEST:  # pragma: no cover
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
        assert issubclass(rv_type, str), \
            f'result must be <class \'str\'> not {rv_type}'
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
