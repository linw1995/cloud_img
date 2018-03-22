import abc
import enum
import json
import logging
from datetime import datetime

import peewee
import yarl


__all__ = ('UploadCfg', 'ImageWithUploadCfg', 'RequestType', 'Adapter')

logger = logging.getLogger(__file__)


class RequestType(enum.Enum):
    GET = 1
    POST = 2


class JSONField(peewee.TextField):
    def db_value(self, value):
        try:
            return json.dumps(value)
        except ValueError as err:
            logger.error('json.dumps fails to encode the value by error: %s',
                         err)
        return None

    def python_value(self, value):
        try:
            return json.loads(value)
        except json.JSONDecodeError as err:
            logger.debug('JSONField fails to get python value by error: %s',
                         err)
        return None


class Adapter(abc.ABCMeta):
    """
    adapting the different clients to perform upload and parse the response.
    """

    @abc.abstractmethod
    async def send(self, url, headers=None, json=None, data=None):
        """send the request to server,
        then recive the response and return it"""

    @abc.abstractmethod
    def query_json(self, querystr):
        pass

    @abc.abstractmethod
    def query_xml(self, querystr):
        pass

    @abc.abstractmethod
    def query_regex(self, querystr):
        pass


class UploadCfg(peewee.Model):
    """
    Upload config for different websites.

    Attributes
    ----------
    name : str
        website's name.
    user : User
        user who own this custom upload config.
    request_url : str
        request_url for upload.
    request_type : RequestType

    request_querystring : Mapping
        url query string
    request_headers : Mapping
        request headers
    request_formdata : Mapping
        request formdata
    image_url_querystr : str
        query the image url from response
    thumbnail_url_querystr : str
        query the thumbnail url from response
    delete_url_querystr : str
        query the delete url from response

    """
    from .user import User
    name = peewee.CharField(max_length=255, null=False)
    user = peewee.ForeignKeyField(User, related_name='servers')

    request_url = peewee.TextField(null=False)
    request_type = peewee.SmallIntegerField(
        default=RequestType.POST, null=False)
    # TODO: using yarl.URL._QUERY_QUOTER to validate the property
    request_querystring = JSONField()
    # TODO: using aio-libs' multidict.CIMultiDict to validate the property
    request_headers = JSONField()
    # TODO: using aiohttp.FormData to validate the property
    request_formdata = JSONField()
    # TODO: request_body is hard to implement

    # query the image's info from the response
    image_url_querystr = peewee.CharField(max_length=255, null=False)
    thumbnail_url_querystr = peewee.CharField(max_length=255)
    delete_url_querystr = peewee.CharField(max_length=255)

    class Meta:
        from . import db_proxy
        database = db_proxy
        db_table = 'upload_cfg'

    async def upload(self, adapter, data):
        """
        Make an aysnchronous image file uploading.

        Parameters
        ----------
        adapter : Adapter
            adopting the different clients to perform the request.
        data : bytes
            image binary data.

        """
        if not isinstance(adapter, Adapter):
            raise ValueError(f"{adapter:!r} should be Adopter's instance.")

        # TODO: format image binary, some func and etc,
        # into querystr, or formdata, or headers

        url = yarl.URL(self.request_url)
        if self.request_querystring:
            url = url.with_query(self.request_querystring)

        await adapter.send(url)

    async def query_response(self, adapter):
        """
        Query the image's info from the response

        Parameters
        ----------
        adapter : Adapter
            adapting the different clients to parse the response.

        Returns
        -------
        dict
            contains image's url, thumbnail_url, delete_url and etc.

        """
        pass


class ImageWithUploadCfg(peewee.Model):
    from .image import Image
    upload_cfg = peewee.ForeignKeyField(UploadCfg, related_name='images')
    image = peewee.ForeignKeyField(Image, related_name='upload_cfgs')

    url = peewee.TextField(null=False)
    thumbnail_url = peewee.TextField()
    delete_url = peewee.TextField()

    created_at = peewee.DateTimeField(default=datetime.utcnow)
    seen_at = peewee.DateTimeField(default=datetime.utcnow)

    class Meta:
        from . import db_proxy
        database = db_proxy
        db_table = 'image_with_upload_cfg'
        indexes = ((('upload_cfg', 'image'), True), )
