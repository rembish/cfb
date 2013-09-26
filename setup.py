#!/usr/bin/env python

from os.path import dirname, join
from setuptools import find_packages, setup

here = dirname(__file__)
readme = open(join(here, 'README'), 'rt').read()

setup(
    name='cfb',
    version='0.1',
    packages=find_packages(),
    url='https://github.com/rembish/cfb',
    license='BSD 2-Clause license',
    author='Alex Rembish',
    author_email='alex@rembish.org',
    description=readme
)
