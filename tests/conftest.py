# -*- encoding: utf-8 -*-


def pytest_addoption(parser):
    parser.addoption("--slow", action="store_true", help="run slow tests")
