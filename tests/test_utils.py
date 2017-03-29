"""
Test utilities
~~~~~~~~~~~~~~
"""
import six
import uuid
import pytest

from collections import OrderedDict
from lxml import etree

from pyvas import utils


str = six.text_type


def test_dict_to_lxml_function():
    id = str(uuid.uuid4())[:40]

    # Use an ordered dict to ensure tostring == tostring
    dct = OrderedDict((
        ("name", "name"),
        ("@tag", "tag_value"),
        ("comment", "comment"),
        ("copy", [("id", id)]),
        ("child", {"@id": id}),
        ("alterable", True),
    ))

    result = utils.dict_to_lxml("request", dct)

    expect = etree.Element("request")
    expect.set("tag", "tag_value")
    etree.SubElement(expect, "name").text = "name"
    etree.SubElement(expect, "comment").text = "comment"
    etree.SubElement(expect, "copy", id=id)
    etree.SubElement(expect, "child", id=id)
    etree.SubElement(expect, "alterable").text = six.text_type(True)

    assert etree.tostring(result) == etree.tostring(expect)

    with pytest.raises(TypeError):
        class Dummy:
            def __str__(self):
                raise TypeError
        utils.dict_to_lxml(Dummy(), {})


def test_lxml_to_dict():
    id = str(uuid.uuid4())[:40]

    expect = etree.Element("request")
    expect.text = "root_text"
    etree.SubElement(expect, "name").text = "name"
    etree.SubElement(expect, "comment").text = "comment"
    etree.SubElement(expect, "copy", id=id)
    etree.SubElement(expect, "alterable").text = six.text_type(True)

    result = utils.lxml_to_dict(expect)

    assert isinstance(result, dict)
    assert result["request"]["name"] == "name"
    assert result["request"]["comment"] == "comment"
    assert result["request"]["copy"]["@id"] == id
    assert result["request"]["alterable"] == six.text_type(True)

    with pytest.raises(TypeError):
        utils.lxml_to_dict(1)
