#!/usr/bin/env python

# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import distutils
from os.path import dirname, join

from setuptools import find_packages, setup

def read(*args):
    return open(join(dirname(__file__), *args)).read()


def compile_translations(self):
    """
    Wrapper around the `run` method of distutils or setuptools commands.

    The method creates the compiled translation files before the `run` method of the superclass is run.
    """
    self.announce("Compiling translations", level=distutils.log.INFO)
    self.run_command('compile_catalog')
    super(self.__class__, self).run()


def command_factory(name, base_class, wrapper_method):
    """Factory method to create a distutils or setuptools command with a patched `run` method."""
    return type(str(name), (base_class, object), {'run': wrapper_method})


exec(open('tornado_server_status/version.py').read())

install_requires = [
]
with open('requirements.txt') as f:
    for i in f:
        install_requires.append(i.strip())
   
tests_require = [
    'coverage',
    'flake8',
    'pydocstyle',
    'pylint',
    'pytest-pep8',
    'pytest-cov',
    # for pytest-runner to work, it is important that pytest comes last in
    # this list: https://github.com/pytest-dev/pytest-runner/issues/11
    'pytest'
]

exec(read('tornado_server_status', 'version.py'))

setup(
    name='tornado_server_status',
    version='0.1.0',  # noqa
    description='A tornado server for monitoring server status',
    long_description=read('README.rst'),
    author='h12345jack',
    author_email='h12345jack@gmail.com',
    url='https://github.com/h12345jack/tornado_server_status',
    packages=find_packages(exclude=['docs', 'tests']),
    entry_points={
        'console_scripts': [
            'tss = tornado_server_status.run_server_status:main',
        ]
    },
    include_package_data=True,
    package_data={
        'tornado_server_status': [
            # When adding files here, remember to update MANIFEST.in as well,
            # or else they will not be included in the distribution on PyPI!
            # 'path/to/data_file',
        ]
    },
    install_requires=install_requires,
    classifiers=[
        'Development Status :: 2 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Internet'
    ],
    test_suite='tests',
    setup_requires=['pytest-runner'],
    tests_require=tests_require
)
