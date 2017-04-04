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
    _uuid = str(uuid.uuid4())[:40]

    # Use an ordered dict to ensure tostring == tostring
    dct = OrderedDict((
        ("name", "name"),
        ("@tag", "tag_value"),
        ("comment", "comment"),
        ("child", {"@id": _uuid}),
        ("alterable", True),
        ("#text", "")
    ))

    result = utils.dict_to_lxml("request", dct)

    expect = etree.Element("request")
    expect.text = ""
    expect.set("tag", "tag_value")
    etree.SubElement(expect, "name").text = "name"
    etree.SubElement(expect, "comment").text = "comment"
    etree.SubElement(expect, "child", id=_uuid)
    etree.SubElement(expect, "alterable").text = str(True)

    assert etree.tostring(result) == etree.tostring(expect)

    with pytest.raises(TypeError):
        class Dummy:
            def __str__(self):
                raise TypeError
        utils.dict_to_lxml(Dummy(), {})


def test_lxml_to_dict():
    _uuid = str(uuid.uuid4())[:40]

    expect = etree.Element("request")
    expect.text = "root_text"
    etree.SubElement(expect, "name").text = "name"
    etree.SubElement(expect, "comment").text = "comment"
    etree.SubElement(expect, "copy", id=_uuid)
    etree.SubElement(expect, "alterable").text = str(True)

    result = utils.lxml_to_dict(expect)

    assert result == {"request": {
        "#text": "root_text",
        "name": "name",
        "comment": "comment",
        "alterable": "True",
        "copy": {"@id": _uuid},
    }}

    with pytest.raises(TypeError):
        utils.lxml_to_dict(1)
