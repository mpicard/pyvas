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

    def callback(x):
        return utils.lxml_to_dict(x)

    response = Response(req=req, resp=resp, callback=callback)

    assert response.ok
    assert isinstance(response.data, dict)
    assert response.data["test_response_callback"]["@status"] == "200"

    def callback(x):
        return "a"

    response = Response(req=req, resp=resp, callback=callback)

    assert response.ok
    assert response.data == "a"


def test_response_exceptions():
    req = Element("bad_request")
    resp = Element("bad_response")
    resp.set("status", "None")
    resp.set("status_test", "reason")

    with pytest.raises(TypeError):
        Response(req=req, resp=resp)

    resp.set("status", "400")

    with pytest.raises(exceptions.ElementExists):
        resp.set("status_text", "asdfasdf exists adsfasdlkf;ja")
        response = Response(req=req, resp=resp)
        assert response.ok is False
        response.raise_for_status()

    with pytest.raises(exceptions.HTTPError):
        resp.set("status_text", "asdfasdf")
        response = Response(req=req, resp=resp)
        assert response.ok is False
        response.raise_for_status()

    with pytest.raises(exceptions.HTTPError):
        resp.set("status", "499")
        resp.set("status_text", "nope")
        response = Response(req=req, resp=resp)
        response.raise_for_status()

    with pytest.raises(exceptions.HTTPError):
        resp.set("status", "500")
        resp.set("status_text", "server")
        response = Response(req=req, resp=resp)
        response.raise_for_status()

    class Dummy(object):
        tag = "dummy"
        data = {"status": "400", "status_text": "dummy"}

        def get(self, key, default=None):
            return self.data.get(key, default)

    with pytest.raises(exceptions.ResultError):
        response = Response(req="req", resp=Dummy())
        response.raise_for_status()
