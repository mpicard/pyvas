#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
pyvas
=====================
An OpenVAS Managment Protocol (OMP) client for Python
"""
from __future__ import absolute_import, print_function

from glob import glob
from os.path import basename
from os.path import splitext

from setuptools import setup
from setuptools import find_packages


setup(
    name="pyvas",
    version="0.2.0",
    description="An OpenVAS Managment Protocol (OMP) v7 client for Python",
    url="https://github.com/mpicard/pyvas",
    author="Martin Picard",
    author_email="martin8768@gmail.com",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Operating System :: Unix",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Utilities",
        "Topic :: Software Development :: Libraries",
        "Topic :: Internet :: WWW/HTTP",
    ],
    keywords="openvas omp client",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    install_requires=["six", "lxml"],
    setup_requires=["pytest-runner"],
    tests_require=["tox"],
)
