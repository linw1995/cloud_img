import json

import peewee
import pytest
from aiohttp.test_utils import make_mocked_coro, sentinel
from lxml import etree

from cloud_img.models.upload_cfg import Adapter, JSONField, UploadCfg


def test_query_fail():
    upload_cfg = UploadCfg()

    with pytest.raises(ValueError):
        upload_cfg.image_url_querystr = '$noknown:abcdef$'
        upload_cfg.query_response('')

    with pytest.raises(ValueError):
        upload_cfg.image_url_querystr = '$noknown$'
        upload_cfg.query_response('')


def test_query_json_response():
    resource = {
        'data': {
            'urls': [
                'https://www.python.org/',
                'https://docs.python.org/',
            ],
            'id': 12,
        }
    }

    response_body = json.dumps(resource)

    upload_cfg = UploadCfg()

    upload_cfg.image_url_querystr = '$json:data.urls[1]$'
    rv = upload_cfg.query_response(response_body)
    assert rv['image_url'] == resource['data']['urls'][0]

    upload_cfg.image_url_querystr = 'http://hostname.com/$json:data.id$.png'
    rv = upload_cfg.query_response(response_body)
    assert rv['image_url'] == 'http://hostname.com/12.png'

    with pytest.raises(ValueError):
        cutted_response_body = response_body[:-2]
        upload_cfg.query_response(cutted_response_body)


def test_query_xml_response():
    resource = etree.Element('data')
    url1 = etree.Element('urls')
    url1.text = 'https://www.python.org/'
    url2 = etree.Element('urls')
    url2.text = 'https://docs.python.org/'
    id1 = etree.Element('id')
    id1.text = '12'
    resource.append(url1)
    resource.append(url2)
    resource.append(id1)

    response_body = etree.tostring(resource)

    upload_cfg = UploadCfg()

    upload_cfg.image_url_querystr = '$xml:data.urls[1]$'
    rv = upload_cfg.query_response(response_body)
    assert rv['image_url'] == url1.text

    upload_cfg.image_url_querystr = 'http://hostname.com/$xml:data.id$.png'
    rv = upload_cfg.query_response(response_body)
    assert rv['image_url'] == 'http://hostname.com/12.png'

    with pytest.raises(ValueError):
        cutted_response_body = response_body[:-2]
        upload_cfg.query_response(cutted_response_body)


def test_query_regex_response():
    response_body = "url1=https://www.python.org/" \
        " url2=https://docs.python.org/" \
        " id=12"

    upload_cfg = UploadCfg()

    upload_cfg.image_url_querystr = r'$regex:url1=(\S+) $'
    rv = upload_cfg.query_response(response_body)
    assert rv['image_url'] == 'https://www.python.org/'

    upload_cfg.image_url_querystr = r'http://hostname.com/$regex:id=(\d+)$.png'
    rv = upload_cfg.query_response(response_body)
    assert rv['image_url'] == 'http://hostname.com/12.png'

    with pytest.raises(ValueError):
        cutted_response_body = response_body[2:-2]
        upload_cfg.query_response(cutted_response_body)


async def test_JSONField(db, db_manager, faker):
    class TestModel(peewee.Model):
        data = JSONField()

        class Meta:
            database = db

    db.set_allow_sync(True)
    TestModel.create_table(True)

    data = {'key': 'value'}

    tm = await db_manager.create(TestModel, data=data)

    tm_from_db = await db_manager.get(TestModel, id=tm.id)

    assert 'key' in tm_from_db.data

    TestModel.drop_table(True)


@pytest.fixture
def Client(mocker):
    def Client(return_value=sentinel, raise_exception=sentinel):
        client = mocker.Mock(spec=Adapter)
        client.send = make_mocked_coro(return_value, raise_exception)
        return client

    return Client


async def test_upload_through_formdata(Client):

    image_data = b'abcdef'

    client = Client("")

    upload_cfg = UploadCfg()
    upload_cfg.request_url = 'http://localhost:80/'
    upload_cfg.request_formdata = {'file': '$input$'}
    await upload_cfg.upload(client, image_data)
    _, kwargs = client.send.call_args
    assert 'file' in kwargs['data']
    assert image_data == kwargs['data']['file']


async def test_upload_with_values_through_formdata(Client):

    image_data = b'abcdef'

    client = Client("")

    upload_cfg = UploadCfg()
    upload_cfg.request_url = 'http://localhost:80/'
    upload_cfg.values = {'authToken': 'abcdef', 'arg1': 1, 'arg2': 2}
    upload_cfg.request_formdata = {
        'arg': 'arg=$authToken$',
        'args': 'arg1=$arg1$;arg2=$arg2$',
    }
    await upload_cfg.upload(client, image_data)
    _, kwargs = client.send.call_args
    data = kwargs['data']
    assert 'arg' in data
    assert data['arg'] == 'arg=abcdef'
    assert 'args' in data
    assert data['args'] == 'arg1=1;arg2=2'


async def test_upload_with_values_in_querystr(Client):
    image_data = b'abcdef'

    client = Client("")

    upload_cfg = UploadCfg()
    upload_cfg.request_url = 'http://localhost:80/'
    upload_cfg.values = {'authToken': 'abcdef', 'arg1': 1, 'arg2': 2}
    upload_cfg.request_querystring = {
        'arg': 'arg=$authToken$',
        'args': 'arg1=$arg1$;arg2=$arg2$',
    }
    await upload_cfg.upload(client, image_data)

    _, kwargs = client.send.call_args
    query_rv = kwargs['url'].query
    assert 'arg' in query_rv
    assert query_rv['arg'] == 'arg=abcdef'
    assert 'args' in query_rv
    assert query_rv['args'] == 'arg1=1;arg2=2'


async def test_upload_with_values_in_headers(Client):
    image_data = b'abcdef'

    client = Client("")

    upload_cfg = UploadCfg()
    upload_cfg.request_url = 'http://localhost:80/'
    upload_cfg.values = {'authToken': 'abcdef', 'arg1': 1, 'arg2': 2}
    upload_cfg.request_headers = {
        'arg': 'arg=$authToken$',
        'args': 'arg1=$arg1$;arg2=$arg2$',
    }
    await upload_cfg.upload(client, image_data)

    _, kwargs = client.send.call_args
    headers = kwargs['headers']
    assert 'arg' in headers
    assert headers['arg'] == 'arg=abcdef'
    assert 'args' in headers
    assert headers['args'] == 'arg1=1;arg2=2'
