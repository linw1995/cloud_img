from cloud_img.utils import check_mysql, check_redis, get_config


def test_check_mysql(app):
    conf = {
        'db': 'test',
        'host': '127.0.0.1',
        'port': 12345,
        'user': 'root',
        'password': 'test',
    }
    is_existed = check_mysql(conf)
    assert is_existed is False

    conf = get_config()['db']['mysql']
    is_existed = check_mysql(conf)
    assert is_existed is True


def test_check_redis(app):
    conf = {
        'db': 0,
        'host': '127.0.0.1',
        'port': 12345,
    }
    is_existed = check_redis(conf)
    assert is_existed is False

    conf = get_config()['db']['redis']
    is_existed = check_redis(conf)
    assert is_existed is True
