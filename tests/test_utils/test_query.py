import pytest
from lxml import etree

from cloud_img.utils import query_json, query_regex, query_xml


def test_query_json():
    resource = {
        'data': {
            'urls': ['https://www.python.org/', 'https://docs.python.org/']
        }
    }

    rv = query_json(resource, 'data.urls[1]')
    assert rv == resource['data']['urls'][0]

    rv = query_json(resource, 'data.urls[2]')
    assert rv == resource['data']['urls'][1]

    with pytest.raises(ValueError):
        query_json(resource, 'data.urls[bor]')

    with pytest.raises(ValueError):
        query_json(resource, 'data.urls[0]')

    with pytest.raises(ValueError):
        query_json(resource, 'data.urls[4]')

    with pytest.raises(ValueError):
        query_json(resource, 'data.url')

    with pytest.raises(ValueError):
        query_json(resource, 'data[1]')

    with pytest.raises(ValueError):
        query_json(resource, 'data')


def test_query_xml():
    resource = etree.Element('data')
    url1 = etree.Element('urls')
    url1.text = 'https://www.python.org/'
    url2 = etree.Element('urls')
    url2.text = 'https://docs.python.org/'
    resource.append(url1)
    resource.append(url2)

    rv = query_xml(resource, 'data.urls[1]')
    assert rv == url1.text

    rv = query_xml(resource, 'data.urls[2]')
    assert rv == url2.text

    with pytest.raises(ValueError):
        query_xml(resource, 'data.urls[bor]')

    with pytest.raises(ValueError):
        query_xml(resource, 'data.urls[0]')

    with pytest.raises(ValueError):
        query_xml(resource, 'data.urls[3]')

    with pytest.raises(ValueError):
        query_xml(resource, 'data.url')

    with pytest.raises(ValueError):
        query_xml(resource, 'data[1]')

    with pytest.raises(ValueError):
        query_xml(resource, 'data')


def test_query_regex():
    resource = "url1=https://www.python.org/" \
        " url2=https://docs.python.org/"

    rv = query_regex(resource, r'url1=(\S+) ')
    assert rv == 'https://www.python.org/'

    rv = query_regex(resource, r'url2=(\S+)')
    assert rv == 'https://docs.python.org/'

    with pytest.raises(ValueError):
        query_regex(resource, r'(no match)')

    with pytest.raises(ValueError):
        query_regex(resource, r'(wrong pattern')
