# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys
import unittest

from rache import (r, schedule_job, delete_job, pending_jobs, scheduled_jobs,
                   REDIS_PREFIX)


if sys.version_info < (2, 7):
    import unittest2 as unittest  # noqa


class ClearRedisTestCase(unittest.TestCase):
    def tearDown(self):  # noqa
        """Clean up the rache:* redis keys"""
        keys = r.keys("{0}*".format(REDIS_PREFIX))
        for key in keys:
            r.delete(key)
    setUp = tearDown


class APITests(ClearRedisTestCase):
    def test_job_data(self):
        schedule_job('fòo', schedule_in=-1, other_arg='lol')
        self.assertEqual(list(pending_jobs()), [{'id': 'fòo',
                                                 'other_arg': 'lol'}])
        self.assertEqual(len(list(pending_jobs())), 0)

    def test_job_deletion(self):
        schedule_job('bar', schedule_in=-1)
        delete_job('bar')
        self.assertEqual(len(list(pending_jobs())), 0)

    def test_schedule_in_future(self):
        schedule_job('lol', schedule_in=10)
        self.assertEqual(len(list(pending_jobs())), 0)
        delete_job('lol')

    def test_reschedule_existing(self):
        schedule_job('lol', schedule_in=-1)
        schedule_job('lol', schedule_in=10)
        self.assertEqual(len(list(pending_jobs())), 0)
        schedule_job('lol', schedule_in=-1)
        self.assertEqual(len(list(pending_jobs())), 1)

    def test_ordering(self):
        schedule_job('foo', schedule_in=-1)
        schedule_job('bar', schedule_in=-2)
        jobs = list(pending_jobs())
        self.assertEqual(jobs[0]['id'], 'bar')
        self.assertEqual(jobs[1]['id'], 'foo')

    def test_reschedule(self):
        schedule_job('baz', schedule_in=-1)
        schedule_job('foo', schedule_in=10)
        jobs = list(pending_jobs(reschedule_in=20))
        self.assertEqual(jobs, [{'id': 'baz'}])

        schedule = list(scheduled_jobs(with_times=True))
        foo = schedule[0]
        baz = schedule[1]
        self.assertEqual(foo[0], ('foo'))
        self.assertEqual(baz[0], ('baz'))
        self.assertEqual(foo[1] + 10, baz[1])

    def test_scheduled_jobs(self):
        schedule_job('jòb', schedule_in=10)
        schedule_job('ötherjòb', schedule_in=20)
        schedule = scheduled_jobs(with_times=True)
        self.assertEqual([s[0] for s in schedule], ['jòb', 'ötherjòb'])
        schedule = list(scheduled_jobs())
        self.assertEqual(schedule, ['jòb', 'ötherjòb'])

    def test_remove_keys(self):
        schedule_job('foobar', schedule_in=-1, attr='stuff', other=12,
                     thing='blah blah')
        jobs = list(pending_jobs())
        self.assertEqual(jobs, [{'id': 'foobar', 'attr': 'stuff',
                                 'other': '12', 'thing': 'blah blah'}])

        schedule_job('foobar', schedule_in=-1, attr=None, other=None,
                     thing='blah blah')
        jobs = list(pending_jobs())
        self.assertEqual(jobs, [{'id': 'foobar', 'thing': 'blah blah'}])

    def test_schedule_without_delay(self):
        with self.assertRaises(TypeError):
            schedule_job('trololol')

    def test_schedule_with_id(self):
        with self.assertRaises(RuntimeError):
            schedule_job('testing', schedule_in=1, id=12)
