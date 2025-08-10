#!/usr/bin/env python

import io
import os
import re

from setuptools import setup, find_packages


def read(*names):
    path = os.path.join(os.path.dirname(__file__), *names)
    with io.open(path, 'r', encoding='utf-8') as fh:
        return fh.read()


def find_version(*names):
    version_file = read(*names)
    match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if match:
        return match.group(1)
    raise RuntimeError('Unable to find version string.')


setup(
    name='sqlparse',
    version=find_version('sqlparse', '__init__.py'),
    description='A non-validating SQL parser.',
    long_description=read('README.rst'),
    author='Andi Albrecht',
    author_email='albrecht.andi@gmail.com',
    url='https://github.com/andialbrecht/sqlparse',
    packages=find_packages(exclude=('tests', 'tests.*')),
    entry_points={'console_scripts': ['sqlformat=sqlparse.__main__:main']},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Database',
        'Topic :: Software Development',
    ],
    python_requires='>=3.2',
)

