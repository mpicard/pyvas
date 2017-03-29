# -*- coding: utf-8 -*-

"""
OpenVAS Manager Protocol v7 Client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from __future__ import unicode_literals, print_function

__title__ = "pyvas"
__version__ = "0.0.2"
__author__ = "Martin Picard"
__license__ = "MIT"
__copyright__ = "Copyright 2016 Martin Picard"


import os
import socket
import ssl
import six
from lxml import etree
from lxml.etree import ElementTree, Element

from .response import Response
from .utils import (dict_to_lxml, lxml_to_dict)
from .exceptions import AuthenticationError, HTTPError


DEFAULT_PORT = os.environ.get("OPENVASMD_PORT", 9390)


def print_xml(response):  # pragma: no cover
    """Debugging print"""
    if isinstance(response, list):
        for item in response:
            print("\n" + etree.tostring(item, pretty_print=True))
    else:
        print("\n" + etree.tostring(response, pretty_print=True))


class Client(object):
    """OpenVAS OMP Client"""

    def __init__(self, host, username=None, password=None, port=DEFAULT_PORT):
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
        """Authenticate Client using username and password."""
        if self.socket is None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket = sock = ssl.wrap_socket(sock)
            sock.connect((self.host, self.port))

        if username is None:
            username = self.username

        if password is None:
            password = self.password

        request = dict_to_lxml(
            "authenticate",
            {"credentials": {
                "username": username,
                "password": password
            }}
        )

        try:
            return self._command(request)
        except HTTPError:
            raise AuthenticationError(username)

    """
    OMP Targets
    """
    def list_targets(self, **kwargs):
        return self._list("targets", **kwargs)

    def get_target(self, id):
        return self._get("target", id=id)

    def create_target(self, name, hosts, comment=None):
        if comment is None:
            comment = ""

        request = dict_to_lxml(
            "create_target",
            {"name": name, "hosts": hosts, "comment": comment}
        )

        return self._create(request)

    def update_target(self, name, hosts, comment=None):

        if comment is None:
            comment = ""

        request = dict_to_lxml(
            "modify_target",
            {}
        )

        return self._update(request)

    def delete_target(self, id):
        return self._delete("target", id=id)

    """
    OMP Configs
    """
    def list_configs(self, **kwargs):
        return self._list("configs", **kwargs)

    def get_config(self, id):
        return self._get("config", id=id)

    def create_config(self, name, copy_id=None, config=None, *args, **kwargs):
        if config:
            raise NotImplemented("Config response copying not supported yet")
        request = dict_to_lxml(
            "create_config",
            {"name": name, "copy": copy_id}
        )
        return self._create(request)

    def update_config(self, *args, **kwargs):
        # TODO
        raise NotImplementedError

    def delete_config(self, id):
        return self._delete("config", id=id)

    """
    OMP Scanners
    """
    def list_scanners(self, **kwargs):
        return self._list("scanners", **kwargs)

    def get_scanner(self, id):
        return self._get("scanner", id=id)

    def create_scanner(self, *args, **kwargs):
        # TODO
        raise NotImplementedError

    def delete_scanner(self, id):
        # TODO
        raise NotImplementedError

    """
    OMP Report Format
    """
    def list_report_formats(self, **kwargs):
        # TODO: filtering kwargs
        return self._list("report_formats", **kwargs)

    def get_report_format(self, id):
        return self._get("report_format", id=id)

    """
    OMP Tasks
    """
    def list_tasks(self, **kwargs):
        # TODO: kwarg filtering
        return self._list("tasks", **kwargs)

    def get_task(self, id):
        return self._get("task", id=id)

    def create_task(self, name, config_id, target_id, scanner_id=None, comment=None):
        if comment is None:
            comment = ""

        if scanner_id is None:
            # Use default scanner
            try:
                scanner_id = self.list_scanners(
                    name="OpenVAS Default"
                )[0]["@id"]
            except (HTTPError, IndexError):
                raise HTTPError()

        request = dict_to_lxml(
            "create_task",
            {
                "name": name,
                "config": [("id", config_id)],
                "target": [("id", target_id)],
                "scanner": [("id", scanner_id)],
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

    def delete_task(self, id):
        return self._delete("task", id=id)

    """
    OMP Reports
    """
    def list_reports(self, **kwargs):
        return self._list("reports", **kwargs)

    def create_report(self, report, task_id=None, task_name=None,
                      task_comment=None, in_assets=True):
        raise NotImplementedError

    def get_report(self, id, **kwargs):
        return self._get('report', id=id)

    def download_report(self, id, format_id=None, as_element_tree=False):
        """Get XML or base64 encoded report contents"""
        request = Element("get_reports")

        request.set("report_id", id)

        if format_id is not None:
            request.set("format_id", format_id)

        response = self._command(request)

        report = response.xml.find("report")

        if report.attrib["content_type"] == "text/xml" or as_element_tree:
            return report
        report = response.find(".//report_format").tail
        try:
            return report.decode("base64")
        except AttributeError:
            return report

    """
    OMP Schedules
    """
    def list_schedules(self, **kwargs):
        return self._list("schedules", **kwargs)

    def create_schedule(self, name, comment=None, copy=None, first_time=None,
                        duration=None, period=None, timezone=None):
        """Create an OpenVAS task schedule"""
        if comment is None:
            comment = ""

        data = {
            "name": name,
            "comment": comment
        }

        if copy is not None:
            data["copy"] = copy

        if first_time is not None:
            data["first_time"] = {
                "minute": first_time.get("minute"),
                "hour": first_time.get("hour"),
                "day_of_month": first_time.get("day_of_month"),
                "year": first_time.get("year")
            }

        if duration is not None:
            data["duration"] = {
                "text": duration.get("duration"),
                "unit": duration.get("unit")
            }

        if period is not None:
            data["period"] = {
                "text": period.get("period"),
                "unit": period.get("unit")
            }

        if timezone is not None:
            data["timezone"] = timezone

        request = dict_to_lxml("create_schedule", data)

        return self._create(request)

    def get_schedule(self, id, **kwargs):
        return self._get('schedule', id=id)

    def update_schedule(self):
        raise NotImplementedError

    def delete_schedule(self, id):
        return self._delete('schedule', id=id)

    """
    Client internal methods
    """
    def _command(self, request, callback=None):
        """Send, build and validate reponse"""
        resp = self._send_request(request)

        response = Response(req=request, resp=resp, callback=callback)
        # validate response, raise exceptions, if any
        response.raise_for_status()

        return response

    def _get(self, data_type, id, callback=None, **kwargs):
        """Generic get function"""
        request = Element("get_{}s".format(data_type))

        request.set("{}_id".format(data_type), id)

        if callback is None:
            def callback(response):
                return list(lxml_to_dict(response.find(data_type)).values())[0]

        return self._command(request, callback)

    def _list(self, data_type, callback=None, **kwargs):
        """Generic list function"""
        request = Element("get_{}".format(data_type))

        request.set("{}_id".format(data_type), kwargs.pop("id", ""))

        if kwargs is not {}:
            def filter_str(k, v):
                return "{}=\"{}\"".format(k, v)
            filters = [filter_str(k, v) for k, v in six.iteritems(kwargs) if v]
            if filters:
                request.set("filter", " ".join(filters))

        response = self._command(request)
        # send request and grab all data_type elements using lxml `findall`
        items = response.xml.findall(data_type[:-1])

        if callback is None:
            def callback(element):
                return list(lxml_to_dict(element).values())[0]

        return [callback(element) for element in items]

    def _create(self, request):
        """generic create function"""
        return self._command(request)

    def _update(self, data_type, **kwargs):
        """Generic update function"""
        request = dict_to_lxml("modify_{}".format(data_type), kwargs)

        return self._command(request)

    def _delete(self, data_type, id, callback=None):
        """Generic delete function"""
        request = Element("delete_{}".format(data_type))

        request.set("{}_id".format(data_type), id)

        return self._command(request)

    def _manage_task(self, request, id=None, name=None):
        """Generic function to manage tasks"""

        if id is None and name:
            id = self.list_tasks(name=name)[0]["@id"]

        request.set("task_id", id)

        return self._command(request)

    def _send_request(self, request):
        """Send XML data to OpenVAS Manager and get results"""

        BLOCK_SIZE = 1024

        if etree.iselement(request):
            root = ElementTree(request)
            root.write(self.socket, encoding="utf-8")

        else:
            if isinstance(request, six.text_type):
                request = request.encode("utf-8")
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
