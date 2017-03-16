from __future__ import unicode_literals, print_function

import uuid
import pytest
from collections import OrderedDict
from lxml import etree, objectify

from pyvas import Client


def setup_module(module):
    module.cli = Client('127.0.0.1')


def test_dict_to_xml_function():
    id = str(uuid.uuid4())[:40]

    # Use an ordered dict to ensure tostring == tostring
    dct = OrderedDict((
        ('name', 'name'),
        ('comment', 'comment'),
        ('copy', [('id', id)]),
        ('alterable', True)))

    result = cli._dict_to_xml('request', dct)

    expect = etree.Element('request')
    etree.SubElement(expect, 'name').text = 'name'
    etree.SubElement(expect, 'comment').text = 'comment'
    etree.SubElement(expect, 'copy', id=id)
    etree.SubElement(expect, 'alterable').text = unicode(True)

    assert etree.tostring(result) == etree.tostring(expect)
