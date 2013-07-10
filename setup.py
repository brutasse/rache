# -*- coding: utf-8 -*-
import sys

from distutils.core import setup
from setuptools import find_packages

with open('README.rst') as readme:
    long_description = readme.read()

with open('requirements.txt') as reqs:
    install_requires = [
        line for line in reqs.read().split('\n') if (line and not
                                                     line.startswith('--'))
    ]

test_require = []
if sys.version_info < (2, 7):
    test_require.append('unittest2')


def get_version():
    with open('rache/version.py') as f:
        __version__ = None
        exec(f.read())
        return __version__
    raise RuntimeError("Version not found")


setup(
    name='rache',
    version=get_version(),
    author='Bruno Renié',
    author_email='bruno@renie.fr',
    packages=find_packages(),
    include_package_data=True,
    url='https://github.com/brutasse/rache',
    license='BSD',
    description='A scheduler backed by Redis with a very simple interface',
    long_description=long_description,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
    ],
    zip_safe=False,
    install_requires=install_requires,
    test_require=test_require,
    test_suite='tests',
)
