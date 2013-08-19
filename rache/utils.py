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

    if parsed_redis.netloc.endswith('unix'):
        del config['port']
        del config['host']
        # the last item of the path could also be just part of the socket path
        try:
            config['db'] = int(os.path.split(path)[-1])
        except ValueError:
            pass
        else:
            path = os.path.join(*os.path.split(path)[:-1])
        config['unix_socket_path'] = path
        if parsed_redis.password:
            config['password'] = parsed_redis.password
    else:
        if path[1:]:
            config['db'] = int(path[1:])
        if parsed_redis.password:
            config['password'] = parsed_redis.password
        if parsed_redis.port:
            config['port'] = int(parsed_redis.port)
        if parsed_redis.hostname:
            config['host'] = parsed_redis.hostname

    return config
