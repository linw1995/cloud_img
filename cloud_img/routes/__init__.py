from aiohttp.web import Application

from .auth import login, signup, logout
from .image import ImageApi
from .upload_cfg import UploadCfgApi


def setup(app: Application):
    """
    Setup app's routers.

    Parameters
    ----------
    app : aiohttp.web.Application
        Mode.PRODUCTION, Mode.DEBUG and Mode.TEST.

    """
    app.router.add_post(r'/login', login)
    app.router.add_post(r'/signup', signup)
    app.router.add_post(r'/logout', logout)

    app.router.add_get(r'/image', ImageApi.get)

    app.router.add_get(r'/upload_cfg', UploadCfgApi.get)
