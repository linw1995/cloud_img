import abc
import json
import logging
import re
import reprlib
from datetime import datetime

import lxml.etree
import peewee
import yarl

from ..utils import query_json, query_regex, query_xml


__all__ = ('UploadCfg', 'ImageWithUploadCfg', 'Adapter')

logger = logging.getLogger(__file__)


class JSONField(peewee.TextField):
    def db_value(self, value):
        try:
            return json.dumps(value)
        except ValueError as err:  # pragma: no cover
            logger.error('json.dumps fails to encode the value by error: %s',
                         err)
        return None

    def python_value(self, value):
        try:
            return json.loads(value)
        except json.JSONDecodeError as err:  # pragma: no cover
            logger.debug('JSONField fails to get python value by error: %s',
                         err)
        return None


class Adapter(abc.ABCMeta):
    """
    adapting the different clients to perform upload and parse the response.
    """

    @abc.abstractmethod
    async def send(self, method, url, headers=None, json=None, data=None):
        """
        send the request to server,
        then recive the response and return the decoded body.

        Parameters
        ----------
        method : method
            request method: 'post', 'get'.
        url : yarl.URL
            upload url.
        headers : dict
            request headers.
        json : dict
            request body, content-type: app*/json.
        data : bytes
            request body, formdata or binary.

        Returns
        -------
        str
            response body

        """


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
        request url for upload.
    request_method : srt
        request method
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
    request_method = peewee.CharField(
        max_length=10, default='post', null=False)
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

    QUERYSTR_PATTERN = re.compile(r'(?P<border>\$)'
                                  r'(?P<content_type>\S+?):(?P<querystr>.+)'
                                  r'(?(border)\$)')

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

    def _query_response(self, response_body, content_type, querystr):
        error_msg = ('response_body {}'.format(reprlib.repr(response_body)) +
                     ' is not able to decode as ')
        if content_type == 'json':

            try:
                resource = json.loads(response_body)
            except json.JSONDecodeError as err:
                raise ValueError(error_msg + 'json data.')

            return query_json(resource, querystr)

        elif content_type == 'xml':

            try:
                resource = lxml.etree.fromstring(response_body)
            except lxml.etree.XMLSyntaxError as err:
                raise ValueError(error_msg + 'xml data.')

            return query_xml(resource, querystr)

        elif content_type == 'regex':
            return query_regex(response_body, querystr)

        raise ValueError(f'content_type {content_type!r} is not supported')

    def query_response(self, response_body):
        """
        Query the image's info from the response

        Parameters
        ----------
        response_body : str
            response body.

        Returns
        -------
        dict
            contains image's url, thumbnail_url, delete_url.

        """

        url_querystrs = dict(
            image_url=self.image_url_querystr,
            thumbnail_url=self.thumbnail_url_querystr,
            delete_url=self.delete_url_querystr)
        rv = {}

        for url_type, url_querystr in url_querystrs.items():
            if not url_querystr:
                rv[url_type] = ''
                continue
            match = self.QUERYSTR_PATTERN.search(url_querystr)
            if match is None:
                raise ValueError(
                    f'{url_type}_querystr {url_querystr!r} is invalid.')

            group = match.groupdict()
            content_type = group.get('content_type')
            querystr = group.get('querystr')
            query_rv = self._query_response(response_body, content_type,
                                            querystr)
            prefix = url_querystr[:match.start()]
            suffix = url_querystr[match.end():]
            rv[url_type] = f'{prefix}{query_rv}{suffix}'

        return rv


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
