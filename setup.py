#!/usr/bin/env python

# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import distutils
import subprocess
from os.path import dirname, join

from setuptools import find_packages, setup
from setuptools.command.sdist import sdist
from wheel.bdist_wheel import bdist_wheel


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


setup(name='tornado_server_status',
      version=__version__,  # noqa
      description='A tornado server for monitoring server status',
      long_description=read('README.rst'),
      author='h12345jack',
      author_email='h12345jack@gmail.com',
      url='https://github.com/h12345jack/tornado_server_status',
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
      include_package_data=True,
      install_requires=install_requires,
      packages=find_packages(include=['tornado_server_status*']),
      test_suite='tests',
      setup_requires=['pytest-runner'],
      tests_require=tests_require,
      cmdclass={
        'sdist': command_factory('SDistCommand', sdist, compile_translations),
        'bdist_wheel': command_factory('BDistWheelCommand', bdist_wheel, compile_translations),
    }
)
