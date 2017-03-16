#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
cloudcix-openvas - An OMP (OpenVAS Management Protocol) client interface for Python.
"""

import os
import socket
import ssl
from lxml import etree
from lxml.etree import ElementTree, Element, SubElement

from .exceptions import *


DEFAULT_PORT = os.environ.get("OPENVASMD_PORT", 9390)


def print_response(response):
    if isinstance(response, list):
        for item in response:
            print("")
            print(etree.tostring(item, pretty_print=True))
    else:
        print(etree.tostring(response, pretty_print=True))



class Client(object):
    """OpenVAS OMP Client"""

    def __init__(self, host, port=DEFAULT_PORT, username=None, password=None):

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.socket = None
        self.session = None
        self.debug = False

    def open(self, username=None, password=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket = sock = ssl.wrap_socket(sock)
        sock.connect((self.host, self.port))
        self.authenticate(username, password)

    def close(self):
        self.socket.close()
        self.socket = None

    def authenticate(self, username=None, password=None):
        """Authenticate Client"""
        if username is None:
            username = self.username
        if password is None:
            password = self.password

        request = self._dict_to_xml(
            "authenticate",
            {"credentials": {"username": username, "password": password}}
        )

        try:
            self._command(request)
        except ClientError:
            raise AuthenticationError(username)

    """
    OMP Configs
    """
    def get_configs(self, name=None):
        # TODO callback
        return self._get('configs', name)

    def update_config(self, name):
        # TODO callback
        return self._update('configs', name=name)

    def delete_config(self, name):
        # TODO callback
        self._delete('config')

    """
    OMP Targets
    """
    def get_targets(self, name=None):
        # TODO: callback
        return self._get('targets', name)

    def create_target(self, name, hosts, comment=None):
        # TODO: validate hosts
        if comment is None:
            comment = ""

        request = self._dict_to_xml(
            "create_target",
            {
                "name": name,
                "hosts": hosts,
                "comment": comment
            }
        )

        return self._create(request)

    def update_target(self, name, hosts, comment=None):
        # TODO: validate hosts
        # TODO: don't send empty values
        if comment is None:
            comment = ""

        request = self._dict_to_xml(
            "modify_target",
            {
                "name": name,
                "hosts": hosts,
                "comment": comment
            }
        )


        return self._command(request)

    def delete_target(self, id):
        # TODO: callback
        return self._delete('target', id=id)

    """
    OMP Report Format
    """
    def get_report_formats(self, name=None):
        return self._get('report_formats', name)

    """
    OMP Tasks
    """
    def get_tasks(self, name=None):
        return self._get('tasks', name)

    def create_task(self, name, config_id, target_id, scanner_id, comment=None):
        # TODO: finish spec
        if comment is None:
            comment = ""

        request = self._dict_to_xml(
            "create_task",
            {
                "name": name,
                "config_id": config_id,
                "target_id": target_id,
                "scanner_id": scanner_id,
                "comment": comment,
            }
        )

        return self._create(request)

    """
    OMP Scanners
    """
    def get_scanners(self, name=None):
        return self._get('scanners', name, lambda x: x.find('scanner/name'))

    """
    Client internal methods
    """

    def _command(self, request):
        response = self._send_request(request)
        return self._validate_response(response)

    def _validate_response(self, response):
        status = response.get('status')
        status_text = response.get('status_text')

        if status is None:
            raise ResultError("Response is missing status code: %s"
                              % etree.tostring(response))

        if status.startswith('4'):
            # print(status, status_text)
            raise ClientError(response.tag, status, status_text)

        elif status.startswith('5'):
            # print(status, status_text)
            raise ServerError(response.tag, status, status_text)

        return response

    def _get(self, data_type, name, callback=None):
        """Generic get function"""
        request = Element('get_{}'.format(data_type))

        if name is not None:
            request.set('name', name)

        # print_response(request)
        response = self._command(request)

        if callback is None:
            callback = lambda x: x

        if name:
            return callback(response)
        else:
            return [callback(i) for i in response]

    def _delete(self, data_type, id):
        """Generic delete function"""
        request = Element('delete_{}'.format(data_type))
        request.set('{}_id'.format(data_type), id)
        return self._command(request)

    def _create(self, request, id_tag=None):
        """generic create function"""
        response = self._command(request)
        if id_tag is None:
            id_tag = "id"
        try:
            return response.attrib[id_tag]
        except Exception as e:
            raise ResultError(response.tag, e)

    def _send_request(self, request):
        """Send XML data to OpenVAS Manager and get results"""

        BLOCK_SIZE = 1024

        if etree.iselement(request):
            root = ElementTree(request)
            root.write(self.socket, encoding='utf-8')

        else:
            if isinstance(request, unicode):
                request = request.encode('utf-8')
            self.socket.send(data)

        parser = etree.XMLTreeBuilder()

        while True:
            response = self.socket.recv(BLOCK_SIZE)
            parser.feed(response)
            if len(response) < BLOCK_SIZE:
                break

        root = parser.close()
        return root

    def __enter__(self):
        """Implements `with` context manager syntax"""
        self.open()
        return self

    def __exit__(self, type, value, tb):
        """Implements `with` context manager syntax"""
        self.close()

    @classmethod
    def _dict_to_xml(cls, root, dct):
        """Convert dict to ElementTree"""
        root = Element(root)
        cls._dict_to_xml_recursive(root, dct)
        return root

    @classmethod
    def _dict_to_xml_recursive(cls, parent, dict_item):

        if isinstance(dict_item, dict):
            for tag, child in dict_item.iteritems():
                if isinstance(child, list):
                    for list_child in child:
                        elem = Element(tag)
                        parent.append(elem)
                        cls._dict_to_xml_recursive(elem, child)
                else:
                    elem = Element(tag)
                    parent.append(elem)
                    cls._dict_to_xml_recursive(elem, child)

        elif isinstance(dict_item, list):
            for key, value in dict_item:
                parent.set(key, value)

        elif dict_item is not None:
            parent.text = unicode(dict_item)
