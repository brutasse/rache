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


def schedule_job(job_id, schedule_in, **kwargs):
    """Schedules a job.

    :param job_id: unique identifier for this job
    :param schedule_in: number of seconds from now in which to schedule the job

    :param **kwargs: parameters to attach to the job, key-value structure.

    schedule_at and schedule_in are mutually exclusive.

    >>> schedule_job('http://example.com/test', schedule_in=10, num_retries=10)
    """
    schedule_at = int(time.time()) + schedule_in

    if 'id' in kwargs:
        raise RuntimeError("'id' is a reserved key for the job ID")

    with r.pipeline() as pipe:
        if schedule_at is not None:
            pipe.zadd(REDIS_KEY, schedule_at, job_id)
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


def delete_job(job_id):
    """Deletes a job.

    :param job_id: unique identifier for this job

    >>> delete_job('http://example.com/test')
    """
    with r.pipeline() as pipe:
        pipe.delete(job_key(job_id))
        pipe.zrem(REDIS_KEY, job_id)
        pipe.execute()


def pending_jobs(reschedule_in=None):
    """Gets the job needing execution.

    :param reschedule_in: number of seconds in which returned jobs should be
    auto-rescheduled. If set to None (default), jobs are not auto-rescheduled.
    """
    job_ids = r.zrangebyscore(REDIS_KEY, 0, int(time.time()))

    with r.pipeline() as pipe:
        if reschedule_in is None:
            for job_id in job_ids:
                pipe.zrem(REDIS_KEY, job_id)
        else:
            schedule_at = int(time.time()) + reschedule_in
            for job_id in job_ids:
                pipe.zadd(REDIS_KEY, schedule_at, job_id)
        pipe.execute()

    with r.pipeline() as pipe:
        for job_id in job_ids:
            pipe.hgetall(job_key(job_id.decode('utf-8')))
        jobs = pipe.execute()
    for job_id, data in izip(job_ids, jobs):
        job_data = {'id': job_id.decode('utf-8')}
        for key, value in data.items():
            job_data[key.decode('utf-8')] = value.decode('utf-8')
        yield job_data


def scheduled_jobs(with_times=False):
    """Gets all jobs in the scheduler.

    :param with_times: whether to return tuples with (job_id, timestamp) or
    just job_id as a list of strings.
    """
    jobs = r.zrangebyscore(REDIS_KEY, 0, sys.maxsize, withscores=with_times)
    for job in jobs:
        if with_times:
            yield job[0].decode('utf-8'), job[1]
        else:
            yield job.decode('utf-8')
