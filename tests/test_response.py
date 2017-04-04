# -*- encoding: utf-8 -*-
"""
Tests for pyvas Response
========================
"""
from __future__ import unicode_literals

import collections
import six
import pytest
from lxml.etree import Element, SubElement, iselement

from pyvas import Response
from pyvas import exceptions
from pyvas import utils


@pytest.fixture()
def response():
    req = Element("test")

    resp = Element("test_response")
    resp.set("status", "200")
    resp.set("status_text", "OK")
    resp.set("test_id", "1234")
    child = SubElement(resp, "child")
    child.set('id', "1234")

    return Response(req=req, resp=resp)


def test_response_init(response):
    # attributes
    assert response.ok
    assert response.status_code is 200
    assert response.command == "test"
    assert iselement(response.xml)
    # data dict elements
    assert response["@test_id"] == "1234"
    assert response["child"]["@id"] == "1234"


def test_response_dict_interface(response):
    assert bool(response) is True
    assert isinstance(iter(response), collections.Iterable)
    assert isinstance(str(response), six.string_types)
    assert repr(response)
    assert response.get("@test_id")
    assert response.update({"new_data": 1}) is None
    assert response.get("new_data") is 1
    response["more"] = 1
    assert response["more"] is 1
    del response["@test_id"]
    assert "@test_id" not in response
    assert response.pop("@test_id", True)


def test_response_callback():
    req = Element("test")
    child = SubElement(req, "child")
    child.set('id', "1234")

    resp = Element("test_response_callback")
    resp.set("status", "200")
    resp.set("status_text", "OK")
    resp.set("test_id", "1234")

    def cb(x):
        return utils.lxml_to_dict(x)

    response = Response(req=req, resp=resp, cb=cb)

    assert response.ok
    assert isinstance(response.data, dict)
    assert response.data["test_response_callback"]["@status"] == "200"

    def cb(x):
        return "a"

    response = Response(req=req, resp=resp, cb=cb)

    assert response.ok
    assert response.data == "a"


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (('x', 'int cast'), TypeError),
        (('400', 'exists'), exceptions.ElementExists),
        (('400', 'bogus'), exceptions.InvalidArgumentError),
        (('404', 'not found'), exceptions.ElementNotFound),
        (('400', 'foo'), exceptions.HTTPError),
        (('500', 'server'), exceptions.ServerError),
    ]
)
def test_response_exceptions(mocker, test_input, expected):
    req = Element('test')
    resp = Element('test_response')
    resp.set('status', test_input[0])
    resp.set('status_text', test_input[1])

    try:
        cb = test_input[2]
    except IndexError:
        cb = None

    with pytest.raises(expected) as exc:
        response = Response(req=req, resp=resp, cb=cb)
        assert not response.ok
        response.raise_for_status()
        assert str(exc)


def test_response_result_error():
    req = Element('test')

    class BadResponse():
        status = '400'
        status_text = 'text'
        tag = 'tag'

        def get(self, value, default=None):
            return getattr(self, value, default)

    with pytest.raises(exceptions.ResultError) as exc:
        Response(req=req, resp=BadResponse())
        assert str(exc)
