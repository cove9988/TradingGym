#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

setup(
    name='tgym',
    version='0.1.15',
    description="Trading Gym is an open-source project for the development of reinforcement learning algorithms in the context of trading.",
    author="cove9988",
    author_email='cove9988@gmail.com',
    url='',
    packages=find_packages(),
    install_requires=[
        'gym',
        'pandas',
        'numpy',
        'matplotlib',
        'finta',
        'stable_baseline3',
        'quantstats',
        'mplfinance'
    ],
    license="MIT license",
    zip_safe=False,
    keywords='tgym'
)
