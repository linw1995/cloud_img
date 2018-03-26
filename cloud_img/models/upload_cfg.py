import abc
import json
import logging
import re
import reprlib
from datetime import datetime

import aiohttp
import lxml.etree
import peewee
import yarl

from ..utils import datetime2unix, query_json, query_regex, query_xml


__all__ = ('UploadCfg', 'ImageWithUploadCfg', 'Adapter', 'Client')

logger = logging.getLogger(__file__)


class JSONField(peewee.TextField):
    def db_value(self, value):
        try:
            return json.dumps(value)
        except ValueError as err:  # pragma: no cover
            logger.error('json.dumps fails to encode the value by error: %s',
                         err)

    def python_value(self, value):
        try:
            return json.loads(value)
        except json.JSONDecodeError as err:  # pragma: no cover
            logger.debug('JSONField fails to get python value by error: %s',
                         err)


class Adapter(abc.ABC):
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


class Client(Adapter):
    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def send(self, method, url, headers=None, data=None):
        async with self.session.request(
                method, url, headers=headers, data=data) as resp:
            response_body = await resp.text()
        return response_body


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
    values : Mapping
        user custom value mapping

        if set authtoken: 'abcdef',
        it will replace $authtoken$ with 'abcdef'
        in request_* field below.

        default:
            input: imagedata
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
    user = peewee.ForeignKeyField(User, related_name='upload_cfgs')

    request_url = peewee.TextField(null=False, default='')
    request_method = peewee.CharField(
        max_length=10, default='post', null=False)
    values = JSONField(default=dict)
    request_querystring = JSONField(default=dict)
    request_headers = JSONField(default=dict)
    request_formdata = JSONField(default=dict)

    # query the image's info from the response
    image_url_querystr = peewee.CharField(
        max_length=255, null=False, default='')
    thumbnail_url_querystr = peewee.CharField(max_length=255, default='')
    delete_url_querystr = peewee.CharField(max_length=255, default='')

    QUERYSTR_PATTERN = re.compile(r'(?P<border>\$)'
                                  r'(?P<content_type>\S+?):(?P<querystr>.+)'
                                  r'(?(border)\$)')
    VALUE_PATTERN = re.compile(r'(?P<border>\$)(?P<key>.+?)(?(border)\$)')
    IMAGE_KEY = 'input'

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
        if not isinstance(adapter, Adapter):  # pragma: no cover
            raise ValueError(f"{adapter:!r} should be Adopter's instance.")

        querystring = self.request_querystring.copy()
        headers = self.request_headers.copy()
        formdata = self.request_formdata.copy()

        def make_repl(assert_msg):
            def repl(match):
                key = match.groupdict().get('key')
                assert key != self.IMAGE_KEY, assert_msg
                rv = self.values.get(key)
                return str(rv) if rv is not None else match.group()

            return repl

        if querystring:
            repl = make_repl('cannot set image data into url query string')
            for name, template in querystring.items():
                querystring[name], _ = self.VALUE_PATTERN.subn(repl, template)

        if headers:
            repl = make_repl('cannot set image data into request headers')
            for name, template in headers.items():
                headers[name], _ = self.VALUE_PATTERN.subn(repl, template)

        if formdata:
            repl = make_repl('cannot concat image bytes with str')
            for name, template in formdata.items():
                match = self.VALUE_PATTERN.match(template)
                if match and match.groupdict().get('key') == self.IMAGE_KEY:
                    formdata[name] = data
                    continue
                formdata[name], _ = self.VALUE_PATTERN.subn(repl, template)

        url = yarl.URL(self.request_url)
        if querystring:
            url = url.with_query(querystring)

        response_body = await adapter.send(
            method=self.request_method,
            url=url,
            headers=headers,
            data=formdata)

        rv = self.query_response(response_body)

        return rv, response_body

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

    image_url = peewee.TextField(null=False, default='')
    thumbnail_url = peewee.TextField(default='')
    delete_url = peewee.TextField(default='')

    created_at = peewee.DateTimeField(default=datetime.utcnow)
    seen_at = peewee.DateTimeField(default=datetime.utcnow)

    class Meta:
        from . import db_proxy
        database = db_proxy
        db_table = 'image_with_upload_cfg'
        indexes = ((('upload_cfg', 'image'), True), )

    def toJSON(self):
        return {
            'image_id': self.image_id,
            'upload_cfg_id': self.upload_cfg_id,
            'image_url': self.image_url,
            'thumbnail_url': self.thumbnail_url,
            'delete_url': self.delete_url,
            'created_at': datetime2unix(self.created_at),
            'seen_at': datetime2unix(self.seen_at),
        }
