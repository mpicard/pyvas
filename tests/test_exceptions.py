# -*- encoding: utf-8 -*-
"""
Tests for pyvas Response
========================
"""
from __future__ import unicode_literals

from pyvas import exceptions


def test_base_error():
    assert exceptions.Error()


def test_result_error():
    exc = exceptions.ResultError("test", "test")
    assert exc
    assert str(exc)


def test_authentication_error():
    assert exceptions.AuthenticationError("test")


def test_request_error():
    assert exceptions.RequestError(response="bad", request="bad")


def test_http_error():
    assert exceptions.HTTPError("reason")


def test_element_exists():
    assert exceptions.ElementExists("")


def test_element_not_found():
    assert exceptions.ElementNotFound("")


def test_invalid_argument():
    assert exceptions.InvalidArgumentError("")


def test_server_error():
    assert exceptions.ServerError("")
