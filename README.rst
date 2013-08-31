RACHE
=====

.. image:: https://travis-ci.org/brutasse/rache.png?branch=master
   :alt: Build Status
   :target: https://travis-ci.org/brutasse/rache

A scheduler backed by `Redis`_ with a very simple interface.

.. _Redis: http://redis.io/

RACHE doesn't handle job execution. It only maintains a list of jobs and their
theoretical execution time. It's up to you to monitor pending jobs and send
them to an actual task queue.

Installation
------------

RACHE works with any Python version from 2.6 to 3.3. You only need a working
Redis server.

::

    pip install rache

Configuration
-------------

By default RACHE connects to Redis on localhost, port 6379, database 0. To
override this, set a ``REDIS_URL`` environment variable::

    REDIS_URL=redis://redis.example.com:6379/2

RACHE prefixes all its Redis keys with ``rache:``. You can override this by
setting the ``RACHE_REDIS_PREFIX`` environment variable.

Usage
-----

::

    import rq

    from rache import schedule_job, pending_jobs

    # Schedule a job now
    schedule_job('http://github.com/brutasse/rache', schedule_in=0, timeout=10)

    # Get pending jobs
    jobs = pending_jobs()

    # Send them to the task queue for immediate execution
    for job in jobs:
        rq.enqueue_job(...)

``schedule_job``
````````````````

::

    schedule_job('job id', schedule_in=<seconds>, connection=None, **kwargs)

A given job ID is unique from the scheduler perspective. Scheduling it twice
results in it being scheduled at the time decided in the last call.

``**kwargs`` can be used to attach data to your jobs. For instance, if you
have jobs to fetch URLs and want to attach a timeout to these jobs::

    schedule_job('http://example.com/test', schedule_in=3600, timeout=10)

The job data is persistent. To remove a key from the data, call
``schedule_job()`` with that key set to None::

    schedule_job('http://example.com/test', schedule_in=3600, timeout=None)

``schedule_in`` is mandatory. This means you can't update an existing job
without rescheduling it.

``connection`` allows you to pass a custom Redis connection object. This is
useful if you have your own connection pooling and want to manage connections
yourself.

``pending_jobs``
````````````````

::

    jobs = pending_jobs(reschedule_in=None, limit=None, connection=None)

(the returned value is a generator)

Fetches the pending jobs and returns a list of jobs. Each job is a dictionnary
with an ``id`` key and its additional data.

``reschedule_in`` controls whether to auto-reschedule jobs in a given time.
This is useful if you have periodic jobs but also want to special-case some
jobs according to their results (``enqueue`` is `rq`_-style syntax)::

    jobs = pending_jobs(reschedule_in=3600)

    for job in jobs:
        enqueue(do_something, kwargs=job)

    def do_something(**kwargs):
        # … do some work

        if some_condition:
            # re-schedule in 30 days
            schedule_job(kwargs['id'], schedule_in=3600 * 24 * 30)

.. _rq: http://python-rq.org/

``limit`` allows you to limit the number of jobs returned. Remaining jobs are
left on schedule, even if they should have been scheduled right now.

``connection`` allows you to pass a custom Redis connection object.

``delete_job``
``````````````

::

    delete_job('<job id>', connection=None)

Removes a job completely from the scheduler.

``connection`` allows you to pass a custom Redis connection object.

``job_details``
```````````````

::

    job_details('<job id>', connection=None)

Returns a dictionnary with the job data. The job ID and scheduled time are
set in the ``id`` and ``schedule_at`` keys of the returned value.

``connection`` allows you to pass a custom Redis connection object.

``scheduled_jobs``
``````````````````

::

    scheduled_jobs(with_times=False, connection=None)

(the returned value is a generator)

Fetches all the job IDs stored in the scheduler. This returns a list of IDs or
a list of ``(job_id, timestamp)`` tuples if ``with_times`` is set to ``True``.

This is useful for syncing jobs between the scheduler and a database, for
instance.

``connection`` allows you to pass a custom Redis connection object.

Contributing
------------

Create a local environment::

    virtualen env
    source env/bin/activate
    pip install -e .

Run the tests::

    python setup.py test

Or for all supported python versions::

    tox

Hack, fix bugs and submit pull requests!

Changelog
---------

* **0.3.1** (2013-08-31):

  * Made ``pending_jobs`` work correctly with both ``Redis`` and
    ``StrictRedis`` clients.

* **0.3** (2013-08-31):

  * Allow passing custom Redis connection objects for fine control on open
    connections.

* **0.2.2** (2013-07-10):

  * Fixed a typo that lead to ``AttributeError`` when retrieving some jobs.

* **0.2.1** (2013-07-03):

  * Allowed ``pending_jobs()`` to return non-unicode data if undecodable bytes
    are passed to ``schedule_job()``.

* **0.2** (2013-06-02):

  * Added ``limit`` kwarg to ``pending_jobs()``.
  * Allowed ``schedule_in`` to be a timedelta alternatively to a number of
    seconds.
  * Added ``job_details()``.
  * Numerical data attached to jobs is cast to ``int()`` when returned.

* **0.1** (2013-06-01):

  * Initial release
