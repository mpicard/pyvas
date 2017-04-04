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
try:  # pragma: no cover
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser

from pyvas import Client, exceptions


HOST = os.environ.get("OPENVAS_HOST")
USERNAME = os.environ.get("OPENVAS_USER")
PASSWORD = os.environ.get("OPENVAS_PASSWORD")
NAME = six.text_type(uuid.uuid4())[:6]
LOCALHOST = "127.0.0.1"


print("\n\n== Environ ==")
print("HOST = {}".format(HOST))
print("=============\n")


slow = pytest.mark.skipif(
    not pytest.config.getoption("--slow"),
    reason="need --slow option to run"
)


@pytest.fixture(scope="module")
def client(request):
    with Client(HOST, username=USERNAME, password=PASSWORD) as cli:
        yield cli


@pytest.fixture(scope="function")
def target(request, client):
    try:
        return client.list_targets(name=NAME).data[0]
    except (exceptions.ElementNotFound, IndexError):
        return client.create_target(name=NAME,
                                    hosts=LOCALHOST,
                                    comment="test")


@pytest.fixture(scope="function")
def config(request, client):
    try:
        return client.list_configs(name="empty").data[0]
    except (exceptions.ElementNotFound, IndexError):
        copy_uuid = client.list_configs(name="empty").data[0]["@id"]
        return client.create_config(name=NAME, copy_uuid=copy_uuid)


@pytest.fixture(scope="function")
def scanner(request, client):
    return client.list_scanners(name="OpenVAS Default").data[0]


@pytest.fixture(scope="function")
def task(request, client, target, config):
    try:
        return client.list_configs(name=NAME + "_fixture",
                                   target_uuid=target["@id"],
                                   config_uuid=config["@id"]).data[0]
    except (exceptions.ElementNotFound, IndexError):
        return client.create_task(name=NAME + "_fixture",
                                  target_uuid=target["@id"],
                                  config_uuid=config["@id"])


@pytest.fixture(scope="function")
def report(request, client):
    report = client.list_reports(task=NAME, owner=USERNAME).data[0]
    print(report)
    return report


@pytest.fixture(scope="function")
def schedule(request, client):
    try:
        return client.list_schedules(name=NAME).data[0]
    except (exceptions.ElementNotFound, IndexError):
        ft = {'minute': 1, 'hour': 2, 'day_of_month': 3, 'year': '2017'}
        return client.create_schedule(name=NAME, first_time=ft, duration=1,
                                      duration_unit='day', period=2,
                                      period_unit='week', timezone='UTC')


def test_environment():
    __tracebackhide__ = True
    if HOST is None:
        pytest.fail("OpenVAS host required in env")
    if USERNAME is None:
        pytest.fail("OpenVAS username required in env")
    if PASSWORD is None:
        pytest.fail("OpenVAS password required in env")


def test_client_authenticate():
    client = Client(HOST)
    client.socket = None

    response = client.authenticate(username=USERNAME, password=PASSWORD)
    assert response.ok

    client.username = USERNAME
    client.password = PASSWORD
    response = client.authenticate()
    assert response.ok

    with pytest.raises(exceptions.AuthenticationError):
        client.authenticate(username=USERNAME, password="fake")


def test_client_send_request(client):
    response = client._send_request("<describe_auth/>")
    assert etree.iselement(response)


class TestClientGenericMethods(object):

    def test_list(self, client):
        response = client._list('target')
        assert response.ok

    def test_get(self, client):
        with pytest.raises(exceptions.ElementNotFound):
            client._get('target',
                        uuid=six.text_type(uuid.uuid4()),
                        cb=lambda x: x)


class TestTargets(object):

    def test_create_target(self, client):
        response = client.create_target(name=NAME,
                                        hosts=LOCALHOST,
                                        comment="test")
        assert response.ok and response.status_code == 201

    def test_list_target(self, client):
        response = client.list_targets()
        assert response.ok
        assert isinstance(response.data, list)

    def test_list_filter_target(self, client):
        response = client.list_targets(name=NAME)
        assert response.ok
        assert isinstance(response.data, list)
        assert response.data[0]["name"] == NAME

    def test_get_target(self, client, target):
        response = client.get_target(uuid=target["@id"])
        assert response.ok
        assert target["name"] == response["name"]
        assert target["@id"] == response["@id"]

    def test_modify_target(self, client, target):
        response = client.modify_target(uuid=target["@id"],
                                        hosts="10.10.10.10",
                                        comment="I was modified, yay!")
        assert response.ok
        # validate new attributes
        target = client.get_target(uuid=target["@id"])
        assert target.ok
        assert target["hosts"] == '10.10.10.10'
        assert target["comment"] == "I was modified, yay!"

    def test_delete_target(self, client, target):
        response = client.delete_target(uuid=target["@id"])
        assert response.ok


class TestConfigs(object):

    def test_create_config(self, client, config):
        response = client.create_config(name=NAME, copy_uuid=config["@id"])
        assert response.ok

    def test_list_config(self, client):
        response = client.list_configs()
        assert response.ok
        assert isinstance(response.data, list)

    def test_list_filter_config(self, client):
        response = client.list_configs(name="Host Discovery")
        assert response.ok
        assert isinstance(response.data, list)
        assert response.data[0]["name"] == "Host Discovery"

    def test_get_config(self, client, config):
        response = client.get_config(uuid=config["@id"])
        assert response.ok
        assert response.get('@id') == config["@id"]

    def test_delete_config(self, client, config):
        empty = client.create_config(name="delete me",
                                     copy_uuid=config["@id"])
        response = client.delete_config(uuid=empty["@id"])
        assert response["@status"] == "200"


class TestScanners(object):

    def test_list_scanner(self, client):
        response = client.list_scanners()
        assert response.ok
        assert isinstance(response.data, list)

    def test_list_filter_scanner(self, client):
        response = client.list_scanners(name="OpenVAS Default")
        assert response.ok
        assert isinstance(response.data, list)
        assert response.data[0]['name'] == 'OpenVAS Default'

    def test_get_scanner(self, client, scanner):
        response = client.get_scanner(uuid=scanner["@id"])
        assert response.ok
        assert response["@id"] == scanner["@id"]
        assert response["name"] == scanner["name"]


class TestReportFormats(object):

    def test_list_report_format(self, client):
        response = client.list_report_formats()
        assert response.ok
        assert isinstance(response.data, list)

    def test_list_filter_report_format(self, client):
        response = client.list_report_formats(name="PDF")
        assert response.ok
        assert isinstance(response.data, list)
        assert response.data[0]["name"] == "PDF"

    def test_get_report_format(self, client):
        report_format = client.list_report_formats(name="PDF").data[0]
        response = client.get_report_format(uuid=report_format["@id"])
        assert response.ok
        assert response.get("@id") == report_format["@id"]


class TestTasks(object):

    def test_create_task(self, mocker, client, config, target):
        response = client.create_task(name=NAME,
                                      target_uuid=target["@id"],
                                      config_uuid=config["@id"])
        assert response
        assert response.ok

        # bad requests
        mocker.patch('pyvas.Client.list_scanners',
                     side_effect=exceptions.ElementNotFound)
        with pytest.raises(exceptions.ElementNotFound):
            response = client.create_task(name=NAME,
                                          target_uuid=target["@id"],
                                          config_uuid=config["@id"])
        mocker.resetall()

        with pytest.raises(exceptions.ElementNotFound):
            response = client.create_task(name=NAME,
                                          comment="comment",
                                          target_uuid=target["@id"],
                                          config_uuid=config["@id"],
                                          scanner_uuid="fake")

    def test_list_tasks(self, client):
        response = client.list_tasks()
        assert response.ok
        assert isinstance(response.data, list)

    def test_get_task(self, client, task):
        response = client.get_task(uuid=task["@id"])
        assert response.ok

    def test_start_task(self, client, task):
        response = client.start_task(uuid=task["@id"])
        assert response.ok

    def test_stop_task(self, client, task):
        response = client.stop_task(uuid=task["@id"])
        assert response.ok

    @slow
    def test_resume_task(self, client, task):
        while True:
            response = client.get_task(uuid=task["@id"])
            print(response.data["status"])
            if response.data['status'].lower() == "new":
                client.start_task(uuid=task["@id"])
            if response.data["status"].lower() == "running":
                client.stop_task(uuid=task["@id"])
            if response.data["status"].lower() == "stopped":
                break
            time.sleep(2)
        response = client.resume_task(uuid=task["@id"])
        assert response.ok

    def test_delet_task(self, client, task):
        response = client.delete_task(uuid=task["@id"])
        assert response.ok


class TestReports(object):

    @slow
    def test_list_reports(self, client):
        response = client.list_reports(task=NAME, owner=USERNAME)
        assert response.ok
        assert isinstance(response.data, list)

    @slow
    def test_get_report(self, client, report):
        response = client.get_report(uuid=report["@id"])
        assert response.ok and response.status_code == 200

    @slow
    def test_download_report_with_xml_format(self, client, report):
        response = client.download_report(uuid=report["@id"])
        assert etree.iselement(response)
        assert response.attrib["id"] == report["@id"]

    @slow
    def test_download_report_with_html_format(self, client, report):
        r_format = client.list_report_formats(name="HTML").data[0]
        response = client.download_report(uuid=report["@id"],
                                          format_uuid=r_format["@id"])
        assert isinstance(response, six.string_types)
        parser = HTMLParser()
        parser.feed(response)
        parser.close()
        assert parser


class TestSchedules(object):

    def test_create_schedule(self, client):
        ft = {'minute': 1, 'hour': 2, 'day_of_month': 3, 'year': '2017'}
        response = client.create_schedule(name=NAME, first_time=ft,
                                          duration=1, duration_unit='day',
                                          period=2, period_unit='week',
                                          timezone='UTC')
        assert response.ok

    def test_get_schedule(self, client, schedule):
        response = client.get_schedule(schedule["@id"])
        assert response.ok
        assert response.get('name') == schedule.get('name')

    def test_list_schedules(self, client):
        response = client.list_schedules()
        assert response.ok
        assert isinstance(response.data, list)

    def test_modify_schedule(self, client, schedule):
        response = client.modify_schedule(uuid=schedule["@id"],
                                          period=3, period_unit='year',
                                          duration=2, duration_unit='week')
        assert response.ok

    def test_delete_schedule(self, client, schedule):
        response = client.delete_schedule(uuid=schedule["@id"])
        assert response.ok
