import asyncio
import logging

from aioredis import create_redis
from pq.server.apps import PulsarQueue, QueueApp, Rpc, RpcServer
from pq.server.consumer import Consumer, Producer

from cloud_img.models import create_db, create_db_manager


class DBMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = self.cfg.params.get('mode')
        self.db_config = self.cfg.params.get('db_config')
        self.db = create_db(self.mode, self.db_config)
        self.db_manager = create_db_manager(self.db)

        async def create_redis_client(uri):
            self.redis_client = await create_redis(uri)

        # attach task into running loop
        asyncio.ensure_future(create_redis_client(self.cfg.get('data_store')))


class ProducerWithDB(DBMixin, Producer):
    pass


class ConsumerWithDB(DBMixin, Consumer):
    pass


class QueueAppWithDB(QueueApp):
    backend_factory = ConsumerWithDB

    def api(self):
        return ProducerWithDB(
            self.cfg,
            logger=self.logger,
        )

    def _start(self, actor, consume=True):  # pragma: no cover
        """
        consumer method, so no cover.
        """
        return ConsumerWithDB(
            self.cfg,
            logger=self.logger,
        ).start(actor, consume)


class PulsarQueueWithDB(PulsarQueue):
    def build(self):
        yield self.new_app(QueueAppWithDB, callable=self.manager)
        wsgi = self.cfg.params.get('wsgi')
        if wsgi:  # pragma: no cover
            if wsgi is True:
                wsgi = Rpc
            yield self.new_app(RpcServer, prefix='rpc', callable=self)


def bg_manager(app):
    from cloud_img.utils import get_config
    config = get_config()['db']['redis']
    if config['password']:  # pragma: no cover
        uri = 'redis://:{password}@{host}:{port}/{db}'.format_map(config)
    else:
        uri = 'redis://{host}:{port}/{db}'.format_map(config)
    cfg = {'task_paths': ['cloud_img.jobs'], 'data_store': uri}
    m = PulsarQueueWithDB(
        cfg=cfg,
        mode=app['mode'],
        db_config=get_config()['db']['mysql'],
    )
    m.console_parsed = False
    m.apps()[0].logger = logging.getLogger(__name__)
    return m


if __name__ == '__main__':
    # create_app to init the configure
    import os
    from cloud_img import create_app
    from cloud_img.constants import ENV_MODE_DEFAULT, ENV_MODE_KEY
    mode = os.environ.get(ENV_MODE_KEY, ENV_MODE_DEFAULT)
    app = create_app(mode)

    m = bg_manager(app)
    m.console_parsed = True
    m.start()
