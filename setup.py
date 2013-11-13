#!/usr/bin/env python

from os.path import dirname, join
from setuptools import find_packages, setup

here = dirname(__file__)
readme = open(join(here, 'README.rst'), 'rt').read()

setup(
    name='cfb',
    version='0.8.3',
    packages=find_packages(),
    url='https://github.com/rembish/cfb',
    license='BSD 2-Clause license',
    author='Alex Rembish',
    author_email='alex@rembish.org',
    description='Microsoft Compound File Binary File Format IO',
    long_description=readme,
    install_requires=['six'],
    test_suite='tests',
    package_data={"tests": ["data/*.doc"]},
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing'))
