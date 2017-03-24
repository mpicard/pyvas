# -*- encoding: utf-8 -*-
# import os
# import uuid
# import pytest


def pytest_addoption(parser):
    parser.addoption("--slow", action="store_true", help="run slow tests")


# @pytest.fixture(scope="session", autouse=True)
# def host():
#     return os.environ.get('OPENVAS_HOST')


# @pytest.fixture(scope="session", autouse=True)
# def username():
#     return os.environ.get('OPENVAS_USER')


# @pytest.fixture(scope="session", autouse=True)
# def password():
#     return os.environ.get('OPENVAS_PASSWORD')


# @pytest.fixture(scope="session", autouse=True)
# def name():
#     return str(uuid.uuid4())[:6]
