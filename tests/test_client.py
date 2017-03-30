# -*- encoding: utf-8 -*-
"""
Tests for pyvas Client
======================
"""
from __future__ import unicode_literals, print_function

import os
import uuid
import time
import six
import pytest
from lxml import etree
try:
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser

from pyvas import Client, exceptions


HOST = os.environ.get("OPENVAS_HOST")
USERNAME = os.environ.get("OPENVAS_USER")
PASSWORD = os.environ.get("OPENVAS_PASSWORD")
NAME = str(uuid.uuid4())[:6]
LOCALHOST = "127.0.0.1"


print("\n\n== Environ ==")
print("NAME = {}".format(NAME))
print("=============\n")


slow = pytest.mark.skipif(
    not pytest.config.getoption("--slow"),
    reason="need --slow option to run"
)


def test_environment():
    __tracebackhide__ = True
    if HOST is None:
        pytest.fail("OpenVAS host required in env")
    if USERNAME is None:
        pytest.fail("OpenVAS username required in env")
    if PASSWORD is None:
        pytest.fail("OpenVAS password required in env")


def test_client_as_context_manager():
    with Client(HOST, username=USERNAME, password=PASSWORD) as cli:
        configs = cli.list_configs()
        assert len(configs) > 2


def test_client_authenticate_error():
    cli = Client(HOST)
    cli.socket = None

    with pytest.raises(exceptions.AuthenticationError):
        cli.authenticate(username=USERNAME, password="fake")


class TestClientBase(object):
    """Abstract TestUnit Base Class for Testing `Client` methods"""

    @classmethod
    def setup_class(cls):
        cls.cli = Client(HOST, username=USERNAME, password=PASSWORD)
        cls.cli.open()

    @classmethod
    def teardown_class(cls):
        cls.cli.close()


class TestTargets(TestClientBase):

    def test_create_target(self):
        response = self.cli.create_target(name=NAME,
                                          hosts=LOCALHOST,
                                          comment="test")
        assert response.ok and response.status_code == 201

    def test_list_target(self):
        try:
            self.cli.create_target(name=NAME, hosts=LOCALHOST)
        except exceptions.ElementExists:
            pass
        response = self.cli.list_targets()
        assert response and isinstance(response, list)

        assert [target for target in response if target["name"] == NAME]

    def test_list_filter_target(self):
        try:
            self.cli.create_target(name=NAME, hosts=LOCALHOST)
        except exceptions.ElementExists:
            pass
        response = self.cli.list_targets(name=NAME)
        assert response[0]["name"] == NAME
        assert response[0]["hosts"] == LOCALHOST

    def test_get_target(self):
        try:
            target = self.cli.create_target(name=NAME, hosts=LOCALHOST)
        except exceptions.ElementExists:
            target = self.cli.list_targets(name=NAME)[0]
        response = self.cli.get_target(uuid=target["@id"])
        assert response.ok
        assert target["name"] == response["name"]
        assert target["@id"] == response["@id"]

    def test_delete_target(self):
        try:
            target = self.cli.create_target(name=NAME, hosts=LOCALHOST)
        except exceptions.ElementExists:
            target = self.cli.list_targets(name=NAME)[0]
        response = self.cli.delete_target(uuid=target["@id"])
        assert response.ok


class TestConfigs(TestClientBase):

    def test_create_config(self):
        copy = self.cli.list_configs(name="empty")[0]
        response = self.cli.create_config(name=NAME, copy_uuid=copy["@id"])
        assert response.ok

    def test_list_config(self):
        response = self.cli.list_configs()
        assert isinstance(response, list)
        assert len(response) > 1

    def test_list_filter_config(self):
        response = self.cli.list_configs(name="Host Discovery")
        assert isinstance(response, list)
        assert len(response) == 1
        assert response[0]["name"] == "Host Discovery"

    def test_get_config(self):
        try:
            config = self.cli.list_configs(name=NAME)[0]
        except IndexError:
            copy = self.cli.list_configs(name="empty")[0]
            config = self.cli.create_config(name=NAME, copy_uuid=copy["@id"])
        response = self.cli.get_config(uuid=config["@id"])
        assert response and config
        assert isinstance(response, dict)
        assert response["name"] == config["name"]
        assert response["@id"] == config["@id"]

    def test_delete_config(self):
        try:
            config = self.cli.list_configs(name=NAME)[0]
        except IndexError:
            copy = self.cli.list_configs(name="empty")[0]
            config = self.cli.create_config(name=NAME, copy_uuid=copy["@id"])
        response = self.cli.delete_config(uuid=config["@id"])
        assert response["@status"] == "200"

    @classmethod
    def teardown_class(cls):
        try:
            config = cls.cli.list_configs(name=NAME)[0]
            cls.cli.delete_config(uuid=config["@id"])
        except IndexError:  # already deleted
            pass
        super(TestConfigs, cls).teardown_class()


class TestScanners(TestClientBase):

    def test_list_scanner(self):
        response = self.cli.list_scanners()
        assert isinstance(response, list)
        assert isinstance(response[0], dict)

    def test_list_filter_scanner(self):
        response = self.cli.list_scanners(name="OpenVAS Default")
        assert isinstance(response, list)
        assert isinstance(response[0], dict)
        assert len(response) == 1

    def test_get_scanner(self):
        try:
            scanner = self.cli.list_scanners(name="OpenVAS Default")[0]
        except Exception as e:
            raise e
        response = self.cli.get_scanner(uuid=scanner["@id"])
        assert response
        assert response["@id"] == scanner["@id"]
        assert response["name"] == scanner["name"]


class TestReportFormats(TestClientBase):

    def test_list_report_format(self):
        response = self.cli.list_report_formats()
        assert isinstance(response, list)
        assert isinstance(response[0], dict)
        assert len(response) > 2

    def test_list_filter_report_format(self):
        response = self.cli.list_report_formats(name="PDF")
        assert response
        assert isinstance(response, list)
        assert len(response) == 1
        assert isinstance(response[0], dict)
        assert response[0]["name"] == "PDF"

    def test_get_report_format(self):
        report_format = self.cli.list_report_formats(name="PDF")[0]
        response = self.cli.get_report_format(uuid=report_format["@id"])
        assert report_format
        assert response
        assert response["@id"] == report_format["@id"]
        assert response["name"] == report_format["name"]


class TestTasks(TestClientBase):

    def test_create_task(self):
        # Use simplest/fatests scan config
        config = self.cli.list_configs(name="Host Discovery")[0]
        try:
            target = self.cli.create_target(name=NAME, hosts=LOCALHOST)
        except exceptions.ElementExists:
            target = self.cli.list_targets(name=NAME)[0]

        response = self.cli.create_task(name=NAME,
                                        target_uuid=target["@id"],
                                        config_uuid=config["@id"])
        assert response
        assert response.ok

    def test_list_tasks(self):
        response = self.cli.list_tasks()
        assert response and isinstance(response, list)
        assert len(response)

    def test_start_task(self):
        try:
            task = self.cli.list_tasks(name=NAME)[0]
        except IndexError:
            # create missing task
            config = self.cli.list_configs(name="Host Discovery")[0]
            try:
                target = self.cli.create_target(name=NAME, hosts=LOCALHOST)
            except exceptions.ElementExists:
                target = self.cli.list_targets(name=NAME)[0]
            task = self.cli.create_task(name=NAME,
                                        target_uuid=target["@id"],
                                        config_uuid=config["@id"])
        try:
            response = self.cli.start_task(uuid=task["@id"])
            assert response
            assert response["@status"] == "202"
            assert response["report_id"]
        except exceptions.HTTPError as e:
            if "active already" in e.response.reason:
                pass

    def test_stop_task(self):
        try:
            task = self.cli.list_tasks(name=NAME)[0]
        except IndexError:
            # create missing task
            config = self.cli.list_configs(name="Host Discovery")[0]
            try:
                target = self.cli.create_target(name=NAME, hosts=LOCALHOST)
            except exceptions.ElementExists:
                target = self.cli.list_targets(name=NAME)[0]
            task = self.cli.create_task(name=NAME,
                                        target_uuid=target["@id"],
                                        config_uuid=config["@id"])

        response = self.cli.stop_task(uuid=task["@id"])
        assert response
        assert response["@status"] == "202"

    def test_get_task(self):
        try:
            task = self.cli.list_tasks(name=NAME)[0]
        except IndexError:
            # create missing task
            config = self.cli.list_configs(name="Host Discovery")[0]
            try:
                target = self.cli.create_target(name=NAME, hosts=LOCALHOST)
            except exceptions.ElementExists:
                target = self.cli.list_targets(name=NAME)[0]
            task = self.cli.create_task(name=NAME,
                                        target_uuid=target["@id"],
                                        config_uuid=config["@id"])

        response = self.cli.get_task(uuid=task["@id"])
        assert response
        assert isinstance(response, dict)
        assert response["@id"] == task["@id"]
        assert response["name"] == task["name"]

    @slow
    def test_resume_task(self):
        try:
            task = self.cli.list_tasks(name=NAME)[0]
        except IndexError:
            # create missing task
            config = self.cli.list_configs(name="Host Discovery")[0]
            try:
                target = self.cli.create_target(name=NAME, hosts=LOCALHOST)
            except exceptions.ElementExists:
                target = self.cli.list_targets(name=NAME)[0]
            task = self.cli.create_task(name=NAME,
                                        target_uuid=target["@id"],
                                        config_uuid=config["@id"])
        try:
            self.cli.start_task(uuid=task["@id"])
        except exceptions.HTTPError as e:
            if "active already" in e.response.reason:
                pass

        while True:
            response = self.cli.get_task(uuid=task["@id"])
            if response["status"] == "Stopped":
                break
            time.sleep(2)
        response = self.cli.resume_task(uuid=task["@id"])
        assert response and response.ok and response.status_code == 202
        assert response["@status"] == "202"

    @slow
    def test_delete_task(self):
        try:
            task = self.cli.list_tasks(name=NAME)[0]
        except IndexError:
            # create missing task
            config = self.cli.list_configs(name="Host Discovery")[0]
            try:
                target = self.cli.create_target(name=NAME, hosts=LOCALHOST)
            except exceptions.ElementExists:
                target = self.cli.list_targets(name=NAME)[0]
            task = self.cli.create_task(name=NAME,
                                        target_uuid=target["@id"],
                                        config_uuid=config["@id"])

        while True:
            response = self.cli.get_task(uuid=task["@id"])
            if response["status"] in ("Done", "Stopped"):
                break
            time.sleep(2)
        response = self.cli.delete_task(uuid=task["@id"])
        assert response and response.ok and response.status_code == 200
        assert response["@status"] == "200"


class TestReports(TestClientBase):

    @slow
    def test_list_reports(self):
        response = self.cli.list_reports(task=NAME, owner=USERNAME)
        assert response
        assert isinstance(response, list)
        assert len(response) >= 1
        assert isinstance(response[0], dict)

    @slow
    def test_get_report(self):
        try:
            report = self.cli.list_reports(task=NAME, owner=USERNAME)[0]
        except IndexError:
            # make task and report
            try:
                task = self.cli.list_tasks(name=NAME)[0]
            except IndexError:
                # create missing task
                config = self.cli.list_configs(name="Host Discovery")[0]
                try:
                    target = self.cli.create_target(name=NAME,
                                                    hosts=LOCALHOST)
                except exceptions.ElementExists:
                    target = self.cli.list_targets(name=NAME)[0]
                task = self.cli.create_task(name=NAME,
                                            target_uuid=target["@id"],
                                            config_uuid=config["@id"])
            content = {"test": "test"}
            report = self.cli.create_report(content, task_uuid=task["@id"])
            assert report and report["@status"] == "201"

        response = self.cli.get_report(uuid=report["@id"])
        assert response.ok and response.status_code == 200

    @slow
    def test_download_report_with_xml_format(self):
        try:
            report = self.cli.list_reports(task=NAME, owner=USERNAME)[0]
        except IndexError:
            assert False
        response = self.cli.download_report(uuid=report["@id"])
        assert etree.iselement(response)
        assert response.attrib["id"] == report["@id"]

    @slow
    def test_download_report_with_html_format(self):
        try:
            report = self.cli.list_reports(task=NAME, owner=USERNAME)[0]
        except IndexError:
            assert False
        report_format = self.cli.list_report_formats(name="HTML")[0]

        response = self.cli.download_report(uuid=report["@id"],
                                            format_uuid=report_format["@id"])
        assert isinstance(response, six.string_types)
        parser = HTMLParser()
        parser.feed(response)
        parser.close()
        assert parser


class TestSchedules(TestClientBase):

    def test_create_schedule(self):
        # TODO
        pass

    def test_list_schedules(self):
        # TODO
        pass

    def test_delete_schedule(self):
        # TODO
        pass

    def test_update_schedule(self):
        # TODO
        pass
