# -*- coding: utf-8 -*-
"""
Tests for pyvas Client
======================
"""
from __future__ import unicode_literals, print_function

import os
import uuid
import time
import datetime
import six
import pytest
from lxml import etree

from pyvas import Client, utils, exceptions


HOST = os.environ.get('OPENVAS_HOST')
USERNAME = os.environ.get('OPENVAS_USER')
PASSWORD = os.environ.get('OPENVAS_PASSWORD')
NAME = str(uuid.uuid4())[:6]


print("\n\n== Environ ==")
print("NAME = {}".format(NAME))
print("=============\n")


class TestClientBase(object):
    """Abstract TestUnit Base Class for Testing `Client` methods"""
    @classmethod
    def setup_class(cls):
        assert HOST
        assert USERNAME
        assert PASSWORD

        cls.cli = Client(HOST, username=USERNAME, password=PASSWORD)
        cls.cli.open()

    @classmethod
    def teardown_class(cls):
        cls.cli.close()


class TestTargets(TestClientBase):

    def test_create_target(self):
        response = self.cli.create_target(name=NAME, hosts="127.0.0.1")
        assert response and isinstance(response, dict)
        assert response['@status'] == '201'

    def test_list_target(self):
        try:
            self.cli.create_target(name=NAME, hosts='127.0.0.1')
        except exceptions.ClientError: # Already exists
            pass
        response = self.cli.list_targets()
        assert response and isinstance(response, list)

        assert [target for target in response if target['name'] == NAME]

    def test_list_filter_target(self):
        try:
            self.cli.create_target(name=NAME, hosts='127.0.0.1')
        except exceptions.ClientError: # Already exists
            pass
        response = self.cli.list_targets(name=NAME)
        assert response[0]['name'] == NAME
        assert response[0]['hosts'] == '127.0.0.1'

    def test_get_target(self):
        try:
            target = self.cli.create_target(name=NAME, hosts='127.0.0.1')
        except exceptions.ClientError: # Already exists
            target = self.cli.list_targets(name=NAME)[0]
        response = self.cli.get_target(id=target["@id"])
        assert isinstance(response, dict)
        assert target["name"] == response["name"]
        assert target["@id"] == response["@id"]

    def test_delete_target(self):
        try:
            target = self.cli.create_target(name=NAME, hosts='127.0.0.1')
        except exceptions.ClientError: # Already exists
            target = self.cli.list_targets(name=NAME)[0]
        response = self.cli.delete_target(id=target['@id'])
        assert response.get('status') == '200'

    @classmethod
    def teardown_class(cls):
        try:
            target = cls.cli.list_targets(name=NAME)[0]
            cls.cli.delete_target(id=target["@id"])
        except IndexError:  # already deleted
            pass
        super(TestTargets, cls).teardown_class()


class TestConfigs(TestClientBase):


    def test_create_config(self):
        copy = self.cli.list_configs(name="empty")[0]
        response = self.cli.create_config(name=NAME, copy_id=copy["@id"])
        assert response["@status"] == "201"
        assert response["@id"]

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
            config = self.cli.create_config(name=NAME, copy_id=config["@id"])
        response = self.cli.get_config(id=config["@id"])
        assert response and config
        assert isinstance(response, dict)
        assert response["name"] == config["name"]
        assert response["@id"] == config["@id"]

    def test_delete_config(self):
        try:
            config = self.cli.list_configs(name=NAME)[0]
        except IndexError:
            copy = self.cli.list_configs(name="empty")[0]
            config = self.cli.create_config(name=NAME, copy_id=config["@id"])
        response = self.cli.delete_config(id=config['@id'])
        assert response.get('status') == '200'

    @classmethod
    def teardown_class(cls):
        try:
            config = cls.cli.list_configs(name=NAME)[0]
            cls.cli.delete_config(id=config["@id"])
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
        response = self.cli.get_scanner(id=scanner["@id"])


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
        response = self.cli.get_report_format(id=report_format["@id"])
        # print(report_format)
        # print(response)
        assert report_format
        assert response
        assert response["@id"] == report_format["@id"]
        assert response["name"] == report_format["name"]


class TestTasks(TestClientBase):

    def test_create_task(self):
        # Use simplest/fatests scan config
        config = self.cli.list_configs(name="Host Discovery")[0]
        try:
            target = self.cli.create_target(name=NAME, hosts="127.0.0.1")
        except exceptions.ClientError:
            target = self.cli.list_targets(name=NAME)[0]

        response = self.cli.create_task(name=NAME,
                                        target_id=target["@id"],
                                        config_id=config["@id"])

    def test_start_task(self):
        try:
            task = self.cli.list_tasks(name=NAME)[0]
        except IndexError:
            # create missing task
            config = self.cli.list_configs(name="Host Discovery")[0]
            try:
                target = self.cli.create_target(name=NAME, hosts="127.0.0.1")
            except exceptions.ClientError:
                target = self.cli.list_targets(name=NAME)[0]
            task = self.cli.create_task(name=NAME,
                                        target_id=target["@id"],
                                        config_id=config["@id"])

        response = self.cli.start_task(id=task["@id"])
        assert response
        assert response["@status"] == "202"
        assert response["report_id"]

    def test_stop_task(self):
        try:
            task = self.cli.list_tasks(name=NAME)[0]
        except IndexError:
            # create missing task
            config = self.cli.list_configs(name="Host Discovery")[0]
            try:
                target = self.cli.create_target(name=NAME, hosts="127.0.0.1")
            except exceptions.ClientError:
                target = self.cli.list_targets(name=NAME)[0]
            task = self.cli.create_task(name=NAME,
                                        target_id=target["@id"],
                                        config_id=config["@id"])

        response = self.cli.stop_task(id=task["@id"])
        assert response
        assert response["@status"] == "202"

    def test_get_task(self):
        try:
            task = self.cli.list_tasks(name=NAME)[0]
        except IndexError:
            # create missing task
            config = self.cli.list_configs(name="Host Discovery")[0]
            try:
                target = self.cli.create_target(name=NAME, hosts="127.0.0.1")
            except exceptions.ClientError:
                target = self.cli.list_targets(name=NAME)[0]
            task = self.cli.create_task(name=NAME,
                                        target_id=target["@id"],
                                        config_id=config["@id"])

        response = self.cli.get_task(id=task["@id"])
        assert response
        assert isinstance(response, dict)
        assert response["@id"] == task["@id"]
        assert response["name"] == task["name"]

    def test_resume_task(self):
        try:
            task = self.cli.list_tasks(name=NAME)[0]
        except IndexError:
            # create missing task
            config = self.cli.list_configs(name="Host Discovery")[0]
            try:
                target = self.cli.create_target(name=NAME, hosts="127.0.0.1")
            except exceptions.ClientError:
                target = self.cli.list_targets(name=NAME)[0]
            task = self.cli.create_task(name=NAME,
                                        target_id=target["@id"],
                                        config_id=config["@id"])

        while True:
            response = self.cli.get_task(id=task["@id"])
            if response["status"] == "Stopped":
                break
            time.sleep(2)
        response = self.cli.resume_task(id=task["@id"])
        assert response
        assert response["@status"] == "202"

class TestReports(TestClientBase):

    def test_list_reports(self):
        response = self.cli.list_reports()
        assert response
        assert isinstance(response, list)
        assert len(response) >= 1
        assert isinstance(response[0], dict)

    # def test_create_report(self):
    #     try:
    #         task = self.cli.list_tasks(name=NAME)[0]
    #     except IndexError:
    #         # create missing task
    #         config = self.cli.list_configs(name="Host Discovery")[0]
    #         try:
    #             target = self.cli.create_target(name=NAME, hosts="127.0.0.1")
    #         except exceptions.ClientError:
    #             target = self.cli.list_targets(name=NAME)[0]
    #         task = self.cli.create_task(name=NAME,
    #                                     target_id=target["@id"],
    #                                     config_id=config["@id"])
    #     report = {'test': 'test'}
    #     response = self.cli.create_report(report, task_id=task["@id"])
    #     assert response and response["@status"] == "201"

    def test_get_report(self):
        try:
            report = self.cli.list_reports()[0]
        except:
            # make task and report
            try:
                task = self.cli.list_tasks(name=NAME)[0]
            except IndexError:
                # create missing task
                config = self.cli.list_configs(name="Host Discovery")[0]
                try:
                    target = self.cli.create_target(name=NAME, hosts="127.0.0.1")
                except exceptions.ClientError:
                    target = self.cli.list_targets(name=NAME)[0]
                task = self.cli.create_task(name=NAME,
                                            target_id=target["@id"],
                                            config_id=config["@id"])
            content = {'test': 'test'}
            report = self.cli.create_report(content, task_id=task["@id"])
            assert report and report["@status"] == "201"

        response = self.cli.get_report(id=report["@id"])
        assert response and response["@status"] == "200"
        assert isinstance(response, dict)



        # response = self.cli.get_report(id=)

# def test_client_as_context_manager():
#     with Client(HOST, username=USERNAME, password=PASSWORD) as cli:
#         configs = cli.list_configs()
#         assert len(configs) > 2


# def test_client_exceptions():
#     with Client(HOST, username=USERNAME, password=PASSWORD) as cli:
#         # with pytest.raises(exceptions.ClientError):
#         #     TODO: find something that returns HTTP 4xx
#         #     pass
#         # with pytest.raises(exceptions.ServerError):
#         #     TODO: find something that returns HTTP 5xx
#         #     pass
#         pass

 # def test_create_report(self):
#         target = self.cli.create_target(name=NAME, hosts="127.0.0.1")
#         config = self.cli.get_config(name="Host Discovery")
#         scanner = self.cli.get_scanner(name="OpenVAS Default")

#         response = self.cli.create_task(name=NAME + "_test_report",
#                                         target_id=target["@id"],
#                                         config_id=config["@id"],
#                                         scanner_id=scanner["@id"])
#         task = self.cli.get_task(id=response["@id"])

#         report_format = self.cli.get_report_format(name="HTML")

#         report = utils.dict_to_xml(
#             "report",
#             {
#                 "@id": str(uuid.uuid4()),
#                 "@format_id": report_format["@id"],
#                 "@extension": "html",
#                 "@content_type": "text/html",
#                 "@type": "scan",
#                 "owner": {"name": USERNAME},
#                 "name": datetime.datetime.now(),
#                 "comment": "",
#                 "creation_time": datetime.datetime.now(),
#                 "modification_time": datetime.datetime.now(),
#                 "writable": "0",
#                 "in_use": "0",
#                 "task": {"@id": task["@id"], "name": task["name"]},
#                 "report_format": {"@id": report_format["@id"],
#                                   "name": report_format["name"]},
#                 "report": "<html></html>".encode('base64'),
#             }
#         )
#         response = self.cli.create_report(report=report, task_name=NAME + "_test_report")

#         assert response["@status"] == "201"

#         with pytest.raises(ValueError):
#             self.cli.create_report(report=123)
#             self.cli.create_report(report={}, task_id="1", task_name="1")
#             self.cli.create_report(report={}, in_assets="nope")


#     def test_list_reports(self):
#         response = self.cli.list_reports()
#         assert response and isinstance(response, list)

#     def test_get_report(self):
#         reports = self.cli.list_reports()
#         report = reports[0]["report"]
#         response = self.cli.get_report(id=report["@id"])
#         assert response and isinstance(response, dict)
