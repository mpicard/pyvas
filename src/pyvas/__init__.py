#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import socket
import ssl
import six
from lxml import etree
from lxml.etree import ElementTree, Element

from .exceptions import (ClientError, ServerError, ResultError,
                         AuthenticationError)
from .utils import (dict_to_xml, xml_to_dict)


DEFAULT_PORT = os.environ.get("OPENVASMD_PORT", 9390)


def print_xml(response):
    # TODO: remove before merge
    if isinstance(response, list):
        for item in response:
            print("")
            print(etree.tostring(item, pretty_print=True))
    else:
        print("\n")
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

        request = dict_to_xml(
            "authenticate",
            {"credentials": {"username": username, "password": password}}
        )

        try:
            self._command(request)
        except ClientError:
            raise AuthenticationError(username)

    """
    OMP Targets
    """

    def list_targets(self, **kwargs):
        return self._list('targets', **kwargs)

    def get_target(self, id):
        return self._get('target', id=id)

    def create_target(self, name, hosts, comment=None):
        # TODO: validate hosts
        if comment is None:
            comment = ""

        request = dict_to_xml(
            "create_target",
            {"name": name, "hosts": hosts, "comment": comment}
        )

        return self._create(request)

    def update_target(self, name, hosts, comment=None):
        # TODO
        raise NotImplemented

    def delete_target(self, id):
        return self._delete('target', id=id)

    """
    OMP Configs
    """

    def list_configs(self, **kwargs):
        return self._list('configs', **kwargs)

    def get_config(self, id):
        return self._get('config', id=id)

    def create_config(self, name, copy_id=None, config=None, *args, **kwargs):
        if config:
            raise NotImplemented("Config response copying not supported yet")
        request = dict_to_xml(
            "create_config",
            {"name": name, "copy": copy_id}
        )
        return self._create(request)

    def update_config(self, *args, **kwargs):
        # TODO
        raise NotImplemented

    def delete_config(self, id):
        return self._delete('config', id=id)

    """
    OMP Scanners
    """

    def list_scanners(self, **kwargs):
        return self._list('scanners', **kwargs)

    def get_scanner(self, id):
        return self._get('scanner', id=id)

    def create_scanner(self, *args, **kwargs):
        # TODO
        raise NotImplemented

    def delete_scanner(self, id):
        # TODO
        raise NotImplemented

    """
    OMP Report Format
    """

    def list_report_formats(self, **kwargs):
        # TODO: filtering kwargs
        return self._list('report_formats', **kwargs)

    def get_report_format(self, id):
        return self._get('report_format', id=id)

    """
    OMP Tasks
    """

    def list_tasks(self, **kwargs):
        # TODO: kwarg filtering
        return self._list('tasks', **kwargs)

    def get_task(self, id):
        return self._get('task', id=id)

    def create_task(self, name, config_id, target_id, scanner_id=None,
                    comment=None):
        # TODO: finish spec
        if comment is None:
            comment = ""

        if scanner_id is None:
            # Use default scanner
            try:
                scanner_id = self.list_scanners(
                    name="OpenVAS Default"
                )[0]["@id"]
            except (ClientError, IndexError):
                raise ClientError("Could not find default scanner, please "
                                  "specify scanner with scanner_id")

        request = dict_to_xml(
            "create_task",
            {
                "name": name,
                "config": [('id', config_id)],
                "target": [('id', target_id)],
                "scanner": [('id', scanner_id)],
                "comment": comment,
            }
        )

        return self._create(request)

    def start_task(self, id=None, name=None):
        request = Element("start_task")
        return self._manage_task(request, id=id, name=name)

    def stop_task(self, id=None, name=None):
        request = Element("stop_task")
        return self._manage_task(request, id=id, name=name)

    def resume_task(self, id=None, name=None):
        request = Element("resume_task")
        return self._manage_task(request, id=id, name=name)

    """
    OMP Reports
    """

    def list_reports(self, **kwargs):
        return self._list('reports', **kwargs)

    def create_report(self, report, task_id=None, task_name=None,
                      task_comment=None, in_assets=True):

        try:
            report = xml_to_dict(report)
        except TypeError:
            if not isinstance(report, dict):
                raise ValueError("report must be a ElementTree or a dict")

        try:
            in_assets = int(in_assets)
        except TypeError:
            raise ValueError("in_assets must be a Boolean")

        command = {"report": report, "in_assets": int(in_assets)}

        request = dict_to_xml("create_report", command)

        if task_id is not None and task_name is None:
            # task for report: id to use existing task
            task = dict_to_xml("task", {"@id": task_id})
        elif task_name is not None and task_id is None:
            # task for report: name to create new task
            task = {"name": task_name}
            if task_comment is not None:
                task.update({"comment": task_comment})
            task = dict_to_xml("task", task)
        elif task_name is None and task_id is None:
            raise ValueError("You must use either task_id or task_name")

        request.append(task)

        response = self._create(request)

        return response

    def get_report(self, id, callback=None, **kwargs):
        request = Element('get_reports')

        request.set('report_id', id)

        response = self._command(request)

        if callback is None:
            def callback(element):
                return xml_to_dict(element).values()[0]

        return callback(response)

    def download_report(self, id):
        """Get XML or base64 encoded report contents"""
        report = self.get_report(id=id)
        # print(report)
        if report["@content_type"] == "text/xml":
            # TODO: return report contents
            return report
        # TODO: investigate why the tail is the content and not the text
        return report.find('.//report_format').tail.decode('base64')

    """
    Client internal methods
    """

    def _command(self, request):
        response = self._send_request(request)
        self._validate_response(response)
        return response

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

    def _get(self, data_type, id, callback=None, **kwargs):
        """Generic get function"""
        # TODO: improve logic, resusability with _list()
        request = Element('get_{}s'.format(data_type))

        request.set('{}_id'.format(data_type), id)

        response = self._command(request)
        # print_xml(request)
        # print_xml(response)

        if callback is None:
            def callback(element):
                return xml_to_dict(element).values()[0]

        return callback(response.find(data_type))

    def _list(self, data_type, callback=None, **kwargs):
        """Generic list function"""
        request = Element('get_{}'.format(data_type))

        request.set('id', kwargs.pop('id', ''))

        if kwargs is not {}:
            def filter_str(k, v):
                return "{}=\"{}\"".format(k, v)
            filters = [filter_str(k, v) for k, v in six.iteritems(kwargs) if v]
            if filters:
                request.set("filter", " ".join(filters))

        # send request and grab all data_type elements using lxml `findall`
        response = self._command(request).findall(data_type[:-1])

        # print_xml(request)                            # TODO: remove b4 merge
        # print_xml(response)                           # TODO: remove b4 merge

        if callback is None:
            def callback(element):
                return xml_to_dict(element).values()[0]

        return [callback(element) for element in response]

    def _create(self, request, id_tag=None):
        """generic create function"""
        response = self._command(request)

        # print_xml(response)

        try:
            # convert to dict and trim unwanted root element
            return xml_to_dict(response).values()[0]
        except Exception as e:
            raise ResultError(response.tag, e)

    def _delete(self, data_type, id):
        """Generic delete function"""
        request = Element('delete_{}'.format(data_type))

        request.set('{}_id'.format(data_type), id)

        return self._command(request)

    def _manage_task(self, request, id=None, name=None):
        """Generic function to manage tasks"""
        if id is None and name:
            task = self.list_tasks(name=name)
            if len(task) == 0:
                id = task[0]["@id"]
            else:
                raise ClientError("404", "Could not find task")

        request.set('task_id', id)

        response = self._command(request)

        return xml_to_dict(response).values()[0]

    def _send_request(self, request):
        """Send XML data to OpenVAS Manager and get results"""

        BLOCK_SIZE = 1024

        if etree.iselement(request):
            root = ElementTree(request)
            root.write(self.socket, encoding='utf-8')

        else:
            if isinstance(request, six.text_type):
                request = request.encode('utf-8')
            self.socket.send(request)

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
