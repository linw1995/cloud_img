import logging

from pq.api import PulsarQueue


def bg_manager():
    from cloud_img.utils import get_config
    config = get_config()['db']['redis']
    if config['password']:  # pragma: no cover
        uri = 'redis://:{password}@{host}:{port}/{db}'.format_map(config)
    else:
        uri = 'redis://{host}:{port}/{db}'.format_map(config)
    cfg = {'task_paths': ['cloud_img.jobs'], 'data_store': uri}
    m = PulsarQueue(cfg=cfg)
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

    m = bg_manager()
    m.console_parsed = True
    m.start()
