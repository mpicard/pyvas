# -*- encoding: utf-8 -*-
"""
pyvas test configuration with pytest
====================================
Using the @slow decorator will skip tests during local testing but run in CI.

Usage:

from conftest import slow

@slow
def test_poorly_coded_slow_test_that_takes_ages_and_ages():
    pass
"""


def pytest_addoption(parser):
    parser.addoption("--slow", action="store_true", help="run slow tests")
