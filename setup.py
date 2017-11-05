#!/usr/bin/env python

from pip.req import parse_requirements
from setuptools import setup, find_packages

requirements = parse_requirements('./requirements.txt', session=False)

setup(
    name='ledslie',
    version="0.0.1",
    description='Led display',
    packages=find_packages(),
    install_requires=[str(requirement.req) for requirement in requirements],
    package_data = {
        'ledslie': [
            'interface/templates/*',
            # 'defaults.conf',
        ],
        'processors': [
            'resources'
        ],
    },
)
