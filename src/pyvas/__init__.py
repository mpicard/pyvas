# -*- coding: utf-8 -*-

"""
OpenVAS Manager Protocol v7 Client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import unicode_literals, print_function

import os
import socket
import ssl
import six
from lxml import etree

from .response import Response
from .utils import (dict_to_lxml, lxml_to_dict)
from .exceptions import AuthenticationError, HTTPError


__title__ = "pyvas"
__version__ = "0.0.2"
__author__ = "Martin Picard"
__license__ = "MIT"
__copyright__ = "Copyright 2017 Martin Picard"


DEFAULT_PORT = os.environ.get("OPENVASMD_PORT", 9390)


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

    def list_targets(self, **kwargs):
        return self._list("targets", **kwargs)

    def get_target(self, uuid):
        return self._get("target", uuid=uuid)

    def create_target(self, name, hosts, comment=None):
        if comment is None:
            comment = ""

        request = dict_to_lxml(
            "create_target",
            {"name": name, "hosts": hosts, "comment": comment}
        )

        return self._create(request)

    def modify_target(self, uuid, **kwargs):
        return self._modify('target', uuid=uuid, exclude_hosts=None, **kwargs)

    def delete_target(self, uuid):
        return self._delete("target", uuid=uuid)

    def list_configs(self, **kwargs):
        return self._list("configs", **kwargs)

    def get_config(self, uuid):
        return self._get("config", uuid=uuid)

    def create_config(self, name, copy_uuid=None, *args, **kwargs):
        request = dict_to_lxml(
            "create_config",
            {
                "name": name,
                "copy": copy_uuid
            }
        )
        return self._create(request)

    def modify_config(self, *args, **kwargs):
        raise NotImplementedError

    def delete_config(self, uuid):
        return self._delete("config", uuid=uuid)

    def list_scanners(self, **kwargs):
        return self._list("scanners", **kwargs)

    def get_scanner(self, uuid):
        return self._get("scanner", uuid=uuid)

    def create_scanner(self, *args, **kwargs):
        raise NotImplementedError

    def delete_scanner(self, uuid):
        raise NotImplementedError

    def list_report_formats(self, **kwargs):
        return self._list("report_formats", **kwargs)

    def get_report_format(self, uuid):
        return self._get("report_format", uuid=uuid)

    def list_tasks(self, **kwargs):
        return self._list("tasks", **kwargs)

    def get_task(self, uuid):
        return self._get("task", uuid=uuid)

    def create_task(self, name, config_uuid, target_uuid,
                    scanner_uuid=None, comment=None):
        """Create a task (aka scan)"""

        if comment is None:
            comment = ""

        if scanner_uuid is None:
            # Use default scanner
            try:
                scanner_uuid = self.list_scanners(
                    name="OpenVAS Default"
                )[0]["@id"]
            except (HTTPError, IndexError):
                raise HTTPError()

        request = dict_to_lxml(
            "create_task",
            {
                "name": name,
                "config": [("id", config_uuid)],
                "target": [("id", target_uuid)],
                "scanner": [("id", scanner_uuid)],
                "comment": comment,
            }
        )

        return self._create(request)

    def start_task(self, uuid):
        request = etree.Element("start_task")
        request.set("task_id", uuid)
        return self._command(request)

    def stop_task(self, uuid):
        request = etree.Element("stop_task")
        request.set("task_id", uuid)
        return self._command(request)

    def resume_task(self, uuid):
        request = etree.Element("resume_task")
        request.set("task_id", uuid)
        return self._command(request)

    def delete_task(self, uuid):
        return self._delete("task", uuid=uuid)

    def list_reports(self, **kwargs):
        return self._list("reports", **kwargs)

    def create_report(self, report, task_uuid=None, task_name=None,
                      task_comment=None, in_assets=True):
        raise NotImplementedError

    def get_report(self, uuid, **kwargs):
        return self._get('report', uuid=uuid)

    def download_report(self, uuid, format_uuid=None, as_element_tree=False):
        """Get XML or base64 encoded report contents"""
        request = etree.Element("get_reports")

        request.set("report_id", uuid)

        if format_uuid is not None:
            request.set("format_id", format_uuid)

        response = self._command(request)

        report = response.xml.find("report")

        if report.attrib["content_type"] == "text/xml" or as_element_tree:
            return report
        report = response.xml.find(".//report_format").tail
        try:
            return report.decode("base64")
        except AttributeError:
            return report

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

    def get_schedule(self, uuid, **kwargs):
        return self._get('schedule', uuid=uuid)

    def modify_schedule(self):
        raise NotImplementedError

    def delete_schedule(self, uuid):
        return self._delete('schedule', uuid=uuid)

    def _command(self, request, callback=None):
        """Send, build and validate response"""
        resp = self._send_request(request)

        response = Response(req=request, resp=resp, callback=callback)
        # valuuidate response, raise exceptions, if any
        response.raise_for_status()

        return response

    def _get(self, data_type, uuid, callback=None, **kwargs):
        """Generic get function"""
        request = etree.Element("get_{}s".format(data_type))

        request.set("{}_id".format(data_type), uuid)

        if callback is None:
            def callback(resp):
                return list(
                    lxml_to_dict(resp.find(data_type)).values()
                )[0]

        return self._command(request, callback)

    def _list(self, data_type, callback=None, **kwargs):
        """Generic list function"""
        request = etree.Element("get_{}".format(data_type))

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
            callback = self._get_default_callback()

        return [callback(element) for element in items]

    def _create(self, request):
        """generic create function"""
        return self._command(request)

    def _modify(self, data_type, uuid, **kwargs):
        """Generic modify function"""
        request = dict_to_lxml("modify_{}".format(data_type), kwargs)

        request.set('{}_id'.format(data_type), uuid)

        return self._command(request)

    def _delete(self, data_type, uuid, callback=None):
        """Generic delete function"""
        request = etree.Element("delete_{}".format(data_type))

        request.set("{}_id".format(data_type), uuid)

        return self._command(request)

    def _send_request(self, request):
        """Send XML data to OpenVAS Manager and get results"""

        block_size = 1024

        if etree.iselement(request):
            root = etree.ElementTree(request)
            root.write(self.socket, encoding="utf-8")

        else:
            if isinstance(request, six.text_type):
                request = request.encode("utf-8")
            self.socket.send(request)

        parser = etree.XMLTreeBuilder()

        while True:
            response = self.socket.recv(block_size)
            parser.feed(response)
            if len(response) < block_size:
                break

        root = parser.close()
        return root

    def __enter__(self):
        """Implements `with` context manager syntax"""
        self.open()
        return self

    def __exit__(self, exc_type, ex_val, exc_tb):
        """Implements `with` context manager syntax"""
        self.close()

    @staticmethod
    def _get_default_callback():
        def callback(element):
            return list(lxml_to_dict(element).values())[0]
        return callback
