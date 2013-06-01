import os

try:
    from urllib import parse
except ImportError:
    import urlparse as parse


def parse_redis_url():
    config = {
        'host': 'localhost',
        'port': 6379,
        'password': None,
        'db': 0,
    }
    parsed_redis = parse.urlparse(
        os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
    if '?' in parsed_redis.path and not parsed_redis.query:
        # Bug in python 2.7.3, fixed in 2.7.4
        path, q, querystring = parsed_redis.path.partition('?')
    else:
        path, q, querystring = parsed_redis.path, None, parsed_redis.query
    if path[1:]:
        config['db'] = int(path[1:])
    querystring = parse.parse_qs(querystring)
    for key in querystring.keys():
        querystring[key] = querystring[key][0]
    for key in config.keys():
        querystring.pop(key, None)
    host, colon, port = parsed_redis.netloc.partition(':')
    if '@' in host:
        password, at, host = host.partition('@')
        config['password'] = password
    config['host'] = host
    config['port'] = int(port)
    return config
