from __future__ import unicode_literals

import os
import sys
import time

try:
    from itertools import izip  # python2
except ImportError:
    izip = zip

import redis

from .utils import parse_redis_url
from .version import __version__  # noqa

REDIS_PREFIX = os.environ.get('RACHE_REDIS_PREFIX', 'rache:')
REDIS_KEY = '{0}queue'.format(REDIS_PREFIX)
REDIS = parse_redis_url()
r = redis.StrictRedis(**REDIS)


def job_key(job_id):
    return '{0}job:{1}'.format(REDIS_PREFIX, job_id).encode('utf-8')


def job_details(job_id, connection=None):
    """Returns the job data with its scheduled timestamp.

    :param job_id: the ID of the job to retrieve."""
    if connection is None:
        connection = r
    data = connection.hgetall(job_key(job_id))

    job_data = {'id': job_id, 'schedule_at': int(connection.zscore(REDIS_KEY,
                                                                   job_id))}
    for key, value in data.items():
        try:
            decoded = value.decode('utf-8')
        except UnicodeDecodeError:
            decoded = value
        if decoded.isdigit():
            decoded = int(decoded)
        job_data[key.decode('utf-8')] = decoded
    return job_data


def schedule_job(job_id, schedule_in, connection=None, **kwargs):
    """Schedules a job.

    :param job_id: unique identifier for this job
    :param schedule_in: number of seconds from now in which to schedule the
    job or timedelta object.

    :param **kwargs: parameters to attach to the job, key-value structure.

    >>> schedule_job('http://example.com/test', schedule_in=10, num_retries=10)
    """
    if not isinstance(schedule_in, int):  # assumed to be a timedelta
        schedule_in = schedule_in.days * 3600 * 24 + schedule_in.seconds
    schedule_at = int(time.time()) + schedule_in

    if connection is None:
        connection = r

    if 'id' in kwargs:
        raise RuntimeError("'id' is a reserved key for the job ID")

    with connection.pipeline() as pipe:
        if schedule_at is not None:
            args = (schedule_at, job_id)
            if isinstance(connection, redis.Redis):
                # StrictRedis or Redis don't have the same argument order
                args = (job_id, schedule_at)
            pipe.zadd(REDIS_KEY, *args)
        delete = []
        hmset = {}
        for key, value in kwargs.items():
            if value is None:
                delete.append(key)
            else:
                hmset[key] = value
        if hmset:
            pipe.hmset(job_key(job_id), hmset)
        if len(delete) > 0:
            pipe.hdel(job_key(job_id), *delete)
        pipe.execute()


def delete_job(job_id, connection=None):
    """Deletes a job.

    :param job_id: unique identifier for this job

    >>> delete_job('http://example.com/test')
    """
    if connection is None:
        connection = r
    with connection.pipeline() as pipe:
        pipe.delete(job_key(job_id))
        pipe.zrem(REDIS_KEY, job_id)
        pipe.execute()


def pending_jobs(reschedule_in=None, limit=None, connection=None):
    """Gets the job needing execution.

    :param reschedule_in: number of seconds in which returned jobs should be
    auto-rescheduled. If set to None (default), jobs are not auto-rescheduled.
    :param limit: max number of jobs to retrieve. If set to None (default),
    retrieves all pending jobs with no limit.
    """
    if connection is None:
        connection = r
    start = None if limit is None else 0
    job_ids = connection.zrangebyscore(REDIS_KEY, 0, int(time.time()),
                                       start=start, num=limit)

    with connection.pipeline() as pipe:
        if reschedule_in is None:
            for job_id in job_ids:
                pipe.zrem(REDIS_KEY, job_id)
        else:
            schedule_at = int(time.time()) + reschedule_in
            for job_id in job_ids:
                args = (schedule_at, job_id)
                if isinstance(connection, redis.Redis):
                    # StrictRedis or Redis don't have the same argument order
                    args = (job_id, schedule_at)
                pipe.zadd(REDIS_KEY, *args)
        pipe.execute()

    with connection.pipeline() as pipe:
        for job_id in job_ids:
            pipe.hgetall(job_key(job_id.decode('utf-8')))
        jobs = pipe.execute()
    for job_id, data in izip(job_ids, jobs):
        job_data = {'id': job_id.decode('utf-8')}
        for key, value in data.items():
            try:
                decoded = value.decode('utf-8')
            except UnicodeDecodeError:
                decoded = value
            if decoded.isdigit():
                decoded = int(decoded)
            job_data[key.decode('utf-8')] = decoded
        yield job_data


def scheduled_jobs(with_times=False, connection=None):
    """Gets all jobs in the scheduler.

    :param with_times: whether to return tuples with (job_id, timestamp) or
    just job_id as a list of strings.
    """
    if connection is None:
        connection = r
    jobs = connection.zrangebyscore(REDIS_KEY, 0, sys.maxsize,
                                    withscores=with_times)
    for job in jobs:
        if with_times:
            yield job[0].decode('utf-8'), job[1]
        else:
            yield job.decode('utf-8')
