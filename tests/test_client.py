# -*- coding: utf-8 -*-
"""
Tests for pyvas Client
======================
"""
from __future__ import unicode_literals

import os
import uuid
import pytest
from lxml import etree

from pyvas import Client


HOST = os.environ.get('OPENVAS_HOST')
USERNAME = os.environ.get('OPENVAS_USER')
PASSWORD = os.environ.get('OPENVAS_PASSWORD')
NAME = str(uuid.uuid4())[:6]


def print_response(response):
    if isinstance(response, list):
        for item in response:
            print("")
            print(etree.tostring(item, pretty_print=True))
    else:
        print(etree.tostring(response, pretty_print=True))


class TestClient:

    @classmethod
    def setup_class(cls):
        cls.cli = Client(HOST, username=USERNAME, password=PASSWORD)
        cls.cli.open()

    @classmethod
    def teardown_class(cls):
        cls.cli.close()

    def test_list_targets(self):
        response = self.cli.get_targets()
        assert response and isinstance(response, list)

    def test_create_target(self):
        target_id = self.cli.create_target(name=NAME, hosts="127.0.0.1")
        assert target_id and isinstance(target_id, basestring)

    def test_get_target(self):
        response = self.cli.get_targets(name=NAME)
        assert etree.iselement(response)
        assert response.find('name').text == NAME

    def test_delete_target(self):
        response = self.cli.get_targets(name=NAME)
        target_id = response.get('id')
        assert len(target_id) == 36
        response = self.cli.delete_target(target_id)
        assert etree.iselement(response)
        assert response.get('status') == '200'

    def test_get_configs(self):
        response = self.cli.get_configs()
        assert response
        assert isinstance(response, list)
        for config in response:
            assert etree.iselement(config)

    def test_get_config(self):
        response = self.cli.get_configs(name="Discovery")
        assert etree.iselement(response)
        assert len(response.get('id')) == 36
        assert response.find('name').text == "Discovery"

    def test_get_scanners(self):
        response = self.cli.get_scanners()
        assert response
        assert isinstance(response, list)
        for scanner in response:
            assert etree.iselement(scanner)

    def test_get_scanner(self):
        response = self.cli.get_scanners(name="OpenVAS Default")
        print_response(response)
        assert etree.iselement(response)
        assert len(response.get('id')) == 36
        assert response.find('name').text == "OpenVAS Default"

    def test_create_task(self):
        # config_id = self.cli.get_configs(name="Discovery")
        # target_id = self.cli.get_targets(name=NAME)
        # scanner_id = self.cli.get_scanners(name="OpenVAS Default")
        # response = self.cli.create_task(name=NAME)
        # print_response(response)
        pass


def test_client_as_context_manager():
    with Client(HOST, username=USERNAME, password=PASSWORD) as cli:
        configs = cli.get_configs()
        assert len(configs)
        for config in configs:
            assert etree.iselement(config)
