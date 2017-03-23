from __future__ import unicode_literals, print_function

import six
import uuid
from collections import OrderedDict
from lxml import etree

from pyvas import utils


def test_dict_to_xml_function():
    id = str(uuid.uuid4())[:40]

    # Use an ordered dict to ensure tostring == tostring
    dct = OrderedDict((
        ('name', 'name'),
        ('@tag', 'tag_value'),
        ('comment', 'comment'),
        ('copy', [('id', id)]),
        ('alterable', True),
    ))

    result = utils.dict_to_xml('request', dct)

    expect = etree.Element('request')
    expect.set('tag', 'tag_value')
    etree.SubElement(expect, 'name').text = 'name'
    etree.SubElement(expect, 'comment').text = 'comment'
    etree.SubElement(expect, 'copy', id=id)
    etree.SubElement(expect, 'alterable').text = six.text_type(True)

    assert etree.tostring(result) == etree.tostring(expect)


def test_xml_to_dict_function():
    id = str(uuid.uuid4())[:40]

    expect = etree.Element('request')
    etree.SubElement(expect, 'name').text = 'name'
    etree.SubElement(expect, 'comment').text = 'comment'
    etree.SubElement(expect, 'copy', id=id)
    etree.SubElement(expect, 'alterable').text = six.text_type(True)

    result = utils.xml_to_dict(expect)

    assert isinstance(result, dict)
    assert result['request']['name'] == 'name'
    assert result['request']['comment'] == 'comment'
    assert result['request']['copy']['@id'] == id
    assert result['request']['alterable'] == six.text_type(True)
