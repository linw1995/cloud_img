import asyncio
import logging

from aioredis import create_redis
from pq.server.apps import PulsarQueue, QueueApp, Rpc, RpcServer
from pq.server.consumer import Consumer, Producer

from cloud_img.models import create_db, create_db_manager
from cloud_img.models.upload_cfg import Client


class SetupMixin:
    """
    SetupMixin setup for the Producer and Consumer.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = self.cfg.params.get('mode')
        self.db_config = self.cfg.params.get('db_config')
        self.db = create_db(self.mode, self.db_config)
        self.db_manager = create_db_manager(self.db)

        async def create_redis_client(uri):
            self.redis_client = await create_redis(uri)

        async def create_http_client():
            self.http_client = Client()

        # attach task into running loop
        asyncio.ensure_future(create_redis_client(self.cfg.get('data_store')))
        asyncio.ensure_future(create_http_client())

    def close(self, msg=None):
        """
        Clean up.
        """
        async def close_redis_client():
            self.redis_client.close()
            await self.redis_client.wait_closed()

        async def close_http_client():
            await self.http_client.close()

        cw_redis_client = asyncio.ensure_future(close_redis_client())
        cw_http_client = asyncio.ensure_future(close_http_client())
        cw_inherit = super(SetupMixin, self).close(msg=msg)

        self._closing_waiter = asyncio.gather(cw_http_client, cw_redis_client,
                                              cw_inherit)
        return self._closing_waiter


class CustomProducer(SetupMixin, Producer):
    pass


class CustomConsumer(SetupMixin, Consumer):
    pass


class CustomQueueApp(QueueApp):
    backend_factory = CustomConsumer

    def api(self):
        return CustomProducer(
            self.cfg,
            logger=self.logger,
        )

    def _start(self, actor, consume=True):  # pragma: no cover
        """
        consumer method, so no cover.
        """
        return CustomConsumer(
            self.cfg,
            logger=self.logger,
        ).start(actor, consume)


class CustomPulsarQueuea(PulsarQueue):
    def build(self):
        yield self.new_app(CustomQueueApp, callable=self.manager)
        wsgi = self.cfg.params.get('wsgi')
        if wsgi:  # pragma: no cover
            if wsgi is True:
                wsgi = Rpc
            yield self.new_app(RpcServer, prefix='rpc', callable=self)


def bg_manager(app):
    from cloud_img.utils import get_config, build_redis_uri
    config = get_config()['db']['redis']
    uri = build_redis_uri(config)
    cfg = {'task_paths': ['cloud_img.jobs'], 'data_store': uri}
    m = CustomPulsarQueuea(
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
