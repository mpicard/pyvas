# -*- encoding: utf-8 -*-
"""
pyvas utilities
~~~~~~~~~~~~~~~
"""

import six
from collections import defaultdict
from lxml.etree import Element


def dict_to_lxml(root, dct):
    """Convert dict to ElementTree"""
    try:
        root = six.text_type(root)
    except Exception:
        raise TypeError("root must be a string")

    def inner_dict_to_xml(parent, dict_item):
        """Recursive dict to ElementTree conversion"""
        if isinstance(dict_item, dict):
            for tag, child in six.iteritems(dict_item):
                if tag.startswith("@"):
                    # Use @tag to set attributes
                    parent.set(tag[1:], child)
                else:
                    elem = Element(tag)
                    parent.append(elem)
                    inner_dict_to_xml(elem, child)

        elif isinstance(dict_item, list):
            # Or use list of tuples to set attributes
            for key, value in dict_item:
                parent.set(key, value)

        elif dict_item is not None:
            parent.text = six.text_type(dict_item)

    root = Element(root)
    inner_dict_to_xml(root, dct)
    return root


def lxml_to_dict(tree):
    """Convert XML ElementTree to dictionary"""
    try:
        d = {tree.tag: {} if tree.attrib else None}
    except AttributeError:
        raise TypeError("tree must be an XML ElementTree")

    children = list(tree)
    if children:
        dd = defaultdict(list)
        for dc in map(lxml_to_dict, children):
            for k, v in six.iteritems(dc):
                dd[k].append(v)
        d = {tree.tag: {k: v[0] if len(v) == 1 else v
                        for k, v in six.iteritems(dd)}}
    if tree.attrib:
        d[tree.tag].update(("@" + k, v) for k, v in six.iteritems(tree.attrib))
    if tree.text:
        text = tree.text.strip()
        if children or tree.attrib:
            if text:
                d[tree.tag]["#text"] = text
        else:
            d[tree.tag] = text
    return d
