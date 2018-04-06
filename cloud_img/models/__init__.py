import logging

import aiomysql
import peewee
import peewee_async

from ..utils import get_config
from ..constants import MODE

db_proxy = peewee.Proxy()

from .image import Image  # noqa: E402
from .upload_cfg import UploadCfg, ImageWithUploadCfg  # noqa: E402
from .user import User  # noqa: E402

__all__ = (
    'setup',
    'create_db',
    'create_db_manager',
    'db_proxy',
    Image,
    ImageWithUploadCfg,
    UploadCfg,
    User,
)

logger = logging.getLogger(__name__)


def create_db(app):
    """
    create database depends on the config.
    """
    conf = get_config()['db']['mysql']

    logger.info('creating db with config: %r', conf)

    database = peewee_async.PooledMySQLDatabase(
        conf['db'],
        host=conf['host'],
        port=conf['port'],
        user=conf['user'],
        password=conf['password'],
        min_connections=conf['minsize'],
        max_connections=conf['maxsize'])

    app['db'] = database

    db_proxy.initialize(database)
    tables = [
        Image,
        ImageWithUploadCfg,
        UploadCfg,
        User,
    ]

    if app['mode'] == MODE.TEST:  # pragma: no cover
        try:
            logger.info('dropping tables: %r', tables)
            database.drop_tables(tables)
        except aiomysql.Warning as warn:
            logger.warning('raise \'%s\' when dropping tables', warn)
        except peewee.InternalError as err:
            logger.error('raise \'%s\' when dropping tables', err)

    logger.info('creating tables: %r', tables)
    # safe=True, means fail silently
    database.create_tables(tables, safe=True)

    # forbid using sync method
    logger.info('forbid using sync method')
    database.set_allow_sync(False)

    return db_proxy


def create_db_manager(app, database):
    """
    create a db_manager to manage the database connections.
    """
    logger.info('creating db_manager')
    manager = peewee_async.Manager(database=database, loop=app.loop)
    app['db_manager'] = manager

    return manager


async def asetup(app):
    """
    asynchronously setup database.
    """
    if app['mode'] != MODE.TEST:  # pragma: no cover
        logger.info('database setup')
        db = create_db(app)
        create_db_manager(app, db)


async def acleanup(app):
    """
    asynchronously cleanup database.
    """
    if app['mode'] != MODE.TEST:  # pragma: no cover
        logger.info('database cleanup')
        await app['db_manager'].close()


def setup(app):
    """
    setup a database for the app.
    """
    app.on_startup.append(asetup)
    app.on_cleanup.append(acleanup)
