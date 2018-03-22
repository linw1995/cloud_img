__version__ = '0.1.0'

from aiohttp import web
from aiohttp_security import CookiesIdentityPolicy, setup as security_setup

from .utils import AuthorizationPolicy, config_setup, log_setup
from .constants import MODE
from .models import setup as db_setup
from .routes import setup as router_setup

__all__ = ('create_app', MODE)


def create_app(mode=MODE.DEBUG):
    """
    Create a different app instance depend on `mode`.

    Parameters
    ----------
    mode : MODE
        MODE.PRODUCTION, MODE.DEBUG and MODE.TEST.

    Returns
    -------
    aiohttp.web.Application
        web app instance.

    """
    app = web.Application()
    app['mode'] = mode

    config_setup(app)
    log_setup(app)
    db_setup(app)
    security_setup(app, CookiesIdentityPolicy(), AuthorizationPolicy(app=app))
    router_setup(app)

    if mode is MODE.DEBUG:  # pragma: no cover
        import aiohttp_debugtoolbar
        aiohttp_debugtoolbar.setup(app)

    return app
