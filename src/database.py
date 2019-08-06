import redis


def test_redis():
    r = redis.Redis(host='localhost', port='6379', db=0)
    r.set('foo', 'bar')
    return r.get('foo')
