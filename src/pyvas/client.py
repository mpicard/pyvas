# -*- encoding: utf-8 -*-
"""
pyvas client
============
usage:

> from pyvas import client
> with client(host, username=username, password=password) as cli:
>     targets = cli.list_targets()
>     if targets.ok:
>         for target in targets:
>             print(target["@id"])
"""

from __future__ import unicode_literals, print_function

import os
import pprint
import socket
import ssl
import six
import sys
from lxml import etree

from .response import Response
from .utils import dict_to_lxml
from .utils import lxml_to_dict
from .exceptions import AuthenticationError
from .exceptions import HTTPError
from .exceptions import ElementNotFound


DEFAULT_PORT = os.environ.get("OPENVASMD_PORT", 9390)
DEFAULT_SCANNER_NAME = "OpenVAS Default"


def print_xml(element):  # pragma: no cover noqa
    """Debug ElementTree dump"""
    print(etree.tostring(element, pretty_print=True))


class Client(object):
    """OpenVAS OMP Client"""

    def __init__(self, host, username=None, password=None, port=DEFAULT_PORT):
        """Initialize OMP client."""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.socket = None
        self.session = None

    def open(self, username=None, password=None):
        """Open socket connection and authenticate client."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket = sock = ssl.wrap_socket(sock)
            sock.connect((self.host, int(self.port)))
            self.authenticate(username, password)
        except:
            sys.stderr.write("Error: cannot connect to OpenVAS host\n")
            raise AuthenticationError

    def close(self):
        """Close client's socket connection to server."""
        self.socket.close()
        self.socket = None

    def authenticate(self, username=None, password=None):
        """Authenticate Client using username and password."""
        if self.socket is None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket = sock = ssl.wrap_socket(sock)
            sock.connect((self.host, int(self.port)))

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

    def list_port_lists(self, **kwargs):
        """Returns list of port lists, filtering via kwargs"""
        return self._list("port_list", **kwargs)

    def get_port_list(self, uuid):
        """Returns a single port list using an @id"""
        return self._get("port_list", uuid=uuid)

    def delete_port_list(self, uuid):
        """Delete a port list."""
        return self._delete("port_list", uuid=uuid)

    def create_port_list(self, name, port_range, comment=None):
        """Creates a list of ports"""
        if comment is None:
            comment = ""

        data = {"name": name, "port_range": port_range, "comment": comment}

        request = dict_to_lxml(
            "create_port_list",
            data
        )

        return self._create(request)

    def list_targets(self, **kwargs):
        """Returns list of targets, filtering via kwargs"""
        return self._list("target", **kwargs)

    def get_target(self, uuid):
        """Returns a single target using an @id."""
        return self._get("target", uuid=uuid)

    def create_target(self, name, hosts, port_list=None, ssh_credential=None, alive_tests=None, comment=None):
        """Creates a target of hosts."""
        if comment is None:
            comment = ""

        data = {"name": name, "hosts": hosts, "comment": comment}
        if port_list:
            data.update({"port_list": {'@id': port_list}})
        if alive_tests:
            data.update({"alive_tests": alive_tests})
        if ssh_credential:
            data.update({"ssh_credential": {'@id': ssh_credential}})

        request = dict_to_lxml(
            "create_target",
            data
        )
        return self._create(request)

    def modify_target(self, uuid, **kwargs):
        """Updates a target with fields in kwargs."""
        return self._modify('target', uuid=uuid, exclude_hosts=None, **kwargs)

    def delete_target(self, uuid):
        """Deletes a target with given id."""
        return self._delete("target", uuid=uuid)

    def map_config_names(self):
        """Return a dictionary of config names mapped to ids."""
        return self._map("config")

    def list_configs(self, **kwargs):
        """List configs and filter using kwargs."""
        return self._list("config", **kwargs)

    def get_config(self, uuid, details=False, families=False, preferences=False, tasks=False):
        """Get config using uuid.
        
        For further details set options to 1:
        * details: get config families, preferences, nvt selectors, and tasks
        * families: include families if details option not selected
        * preferences: include preferences (including list of NVTs) if details option not selected
        * tasks: include tasks using this config if details option not selected
        """
        d = f = p = t ='0'
        if details:
            d = '1'
        if families:
            f = '1'
        if preferences:
            p = '1'
        if tasks:
            t = '1'
        request = etree.Element("get_configs", 
            config_id=uuid, 
            details=d, 
            families=f, 
            preferences=p, 
            tasks=t)
        resp = self._send_request(request)
        response = Response(req=request, resp=resp, cb=None)
        # validate response, raise exceptions, if any
        response.raise_for_status()
        
        return response['config']       

    def get_config_by_name(self, config, **kwargs):
        """Get config using name."""
        return self.get_config(self.map_config_names()[config], **kwargs)

    def list_config_nvts(self, uuid, families=False):
        """Returns a list of oids of nvts called by the given config."""
        try:
            config = self.get_config(uuid, details=True)
            nvts = []
            for n in config['nvt_selectors']['nvt_selector']:
                if n['type'] is '2':
                    nvts += [n['family_or_nvt']]
            if families == True:
                nvt_map = self.map_nvts()
                for fam in self.list_config_families(uuid):
                    for n in nvt_map[fam]:
                        nvts += [n['oid']]
            return nvts
        except:
            return []
        nvt
    def list_config_families(self, uuid):
        """Returns a list of oids of nvt families called by the given config."""
        try:
            config = self.get_config(uuid, families=True)
            families = []
            for family in config['families']['family']:
                if family['name'] != '':
                    families += [family['name']]
            return families
        except:
            return []

    def create_config(self, name, copy_uuid=None, **kwargs):
        """Creates a new config or copies an existing config using the id of
        a config using copy_uuid."""
        data = {"name": name}
        if copy_uuid is not None:
            data["copy"] = copy_uuid
        data.update(kwargs)
        request = dict_to_lxml("create_config", data)
        return self._create(request)
        
    def copy_config_by_name(self, original, copy):
        """Creates a new config by copying an existing one 
        referred to by name"""
        return self.create_config(copy, copy_uuid=self.map_config_names()[original])

    def copy_config_with_blacklist_by_name(self, original, copy, blacklist):
        """
        Copies a config by name, but without the NVTs specified in the 
        blacklist argument.
        """
        original_id = self.map_config_names()[original]
        
        # Query the original config for its NVT preferences
        response = self.get_config_by_name(original, preferences=True)
        preferences = response["preferences"]["preference"]
        
        # Get lists of families, and other NVTs from the original
        # config.
        original_families = self.list_config_families(original_id)
        original_nvts     = self.list_config_nvts(original_id, families=True)
        
        # Make a list of NVTs from the original minus those on 
        # the blacklist
        nvts = list(set(original_nvts) - set(blacklist))
        if len(blacklist) > 0:
            assert len(nvts) < len(original_nvts)
            
        # get a mapping of NVTs to their families
        nvt_to_fam =  self.map_nvts_to_families()

        # Construct model of the new config's NVTs
        # Keys: family names
        # Values: lists of remaining NVTs
        families={}
        for nvt in nvts:
            if nvt not in blacklist:
                family = nvt_to_fam[nvt]
                if family in families.keys():
                    families[family] += [nvt]
                else:
                    families[family] = [nvt]
        
        # Create the new empty config
        response = self.copy_config_by_name("empty", copy)
        copy_id = self.map_config_names()[copy]
        
        # Add the NVTs and preferences to the new config
        for family in families.keys():
            # Add the NVTs
            cmd = etree.Element("modify_config", config_id=copy_id)
            sel = etree.Element("nvt_selection")
            fam = etree.Element("family")
            fam.text = family
            sel.append(fam)
            for n in families[family]:
                if n not in blacklist:
                    etree.SubElement(sel, "nvt", oid=n)
            cmd.append(sel)
            print(etree.tostring(cmd, pretty_print=True))
            print()
            self._command(cmd)
            
        #for nvt in preferences:
            #if nvt['nvt']['@oid'] not in blacklist \
                #and nvt['nvt']['@oid'] != '' \
                #and nvt['value']:
                ## Add the preferences
                #cmd = etree.Element("modify_config", config_id=copy_id)
                #pref = etree.Element('preference')
                #etree.SubElement(pref, 'nvt', oid=nvt['nvt']['@oid'])
                #etree.SubElement(pref, 'name').text = nvt['name']
                ##etree.SubElement(pref, 'name').text = ''
                #etree.SubElement(pref, 'value').text = nvt['value']
                #cmd.append(pref)
                ##print(etree.tostring(cmd))
                #try:
                    #self._command(etree.tostring(cmd))
                #except:
                    #print(etree.tostring(cmd))
                    #print(nvt['name'])
        return copy_id
                


    def delete_config(self, uuid):
        """Delete a config with uuid."""
        return self._delete("config", uuid=uuid)
        
        
    def config_remove_nvt(self, config, nvt):
        """Removes an NVT from the given config"""
        # find the family of the NVT
        families = self.map_nvts()
        
        # reverse the mapping and limit it to the NVTs in this config
        all_my_nvts = self.list_config_nvts(config)
        oid_to_fam = {}
        family = ''
        for f in families.keys():
            for n in families[f]:
                if n["oid"] is nvt:
                    # pick up which family our unwanted NVT belongs to
                    family = f
                    print("family is: {}".format(family))
                if n["oid"] in all_my_nvts:
                    oid_to_fam[n["oid"]] = f
        family = oid_to_fam[nvt]
        assert family is not '', \
            "couldn't determine the family of NVT {}".format(nvt)
            
        # make a list of the remaining NVTs in the unwanted NVT's family
        nvts_to_keep = []
        for n in oid_to_fam.keys():
            if oid_to_fam[n] is family and n is not nvt:
                nvts_to_keep += [n]

        # craft an XML query to nullify the NVT family in the config
        cmd = etree.Element("modify_config", config_id=config)
        sel = etree.Element("family_selection")
        grw = etree.Element("growing")
        grw.text = "1"
        fam = etree.Element("family")
        etree.SubElement(fam, "name").text = family
        etree.SubElement(fam, "all").text = "0"
        etree.SubElement(fam, "growing").text = "0"
        sel.append(grw)
        sel.append(fam)
        cmd.append(sel)
        print(etree.tostring(cmd, pretty_print=True))
        self._command(cmd)
    

        # craft an XML query to set the config's NVTs for that family
        cmd = etree.Element("modify_config", config_id=config)
        sel = etree.Element("nvt_selection")
        fam = etree.Element("family")
        fam.text = family
        sel.append(fam)
        for n in nvts_to_keep:
            if n != nvt:
                etree.SubElement(sel, "nvt", oid=n)
        cmd.append(sel)
        print(etree.tostring(cmd, pretty_print=True))
                            
        # Run this XML
        return self._command(cmd)
        
    def delete_config_by_name(self, config):
        """Delete a config using its name."""
        return self._delete("config", self.map_config_names()[config])

    def list_scanners(self, **kwargs):
        """List scanners and filter using kwargs."""
        return self._list("scanner", **kwargs)

    def get_scanner(self, uuid):
        """Get scanner with uuid."""
        return self._get("scanner", uuid=uuid)

    def list_report_formats(self, **kwargs):
        """List report formats with kwargs filters."""
        return self._list("report_format", **kwargs)

    def get_report_format(self, uuid):
        """Get report format with uuid."""
        return self._get("report_format", uuid=uuid)

    def create_credential(self, name, login, password):
        data = {
            "name": name,
            "login": login,
            "password": password
        }
        request = dict_to_lxml("create_credential", data)

        # print_xml(request)

        return self._create(request)

    def list_tasks(self, **kwargs):
        """List tasks with kwargs filtering."""
        return self._list("task", **kwargs)
        
    def map_task_names(self):
        """Return a dictionary of task names mapped to ids."""
        return self._map("task")
    
    def get_task(self, uuid):
        """Get task with uuid."""
        return self._get("task", uuid=uuid)

    def create_task(self, name, config_uuid, target_uuid,
                    scanner_uuid=None, comment=None, schedule_uuid=None):
        """Create a task."""

        if scanner_uuid is None:
            # try to use default scanner
            try:
                scanners = self.list_scanners(name=DEFAULT_SCANNER_NAME)
                scanner_uuid = scanners[0]["@id"]
            except (ElementNotFound, IndexError, KeyError):
                raise ElementNotFound('''Could not find default scanner,
                                      please use scanner_uuid to specify a
                                      scanner.''')
        data = {
            "name": name,
            "config": {"@id": config_uuid},
            "target": {"@id": target_uuid},
            "scanner": {"@id": scanner_uuid},
        }

        if schedule_uuid is not None:
            data.update({"schedule": {"@id": schedule_uuid}})

        if comment is not None:
            data.update({"comment": comment})

        request = dict_to_lxml("create_task", data)

        # print_xml(request)

        return self._create(request)

    def start_task(self, uuid):
        """Start a task."""
        request = etree.Element("start_task")
        request.set("task_id", uuid)
        return self._command(request)
        
    def start_task_by_name(self, task_name):
        """Start a task by name."""
        self.start_task(self.map_task_names()[task_name])

    def stop_task(self, uuid):
        """stop a task."""
        request = etree.Element("stop_task")
        request.set("task_id", uuid)
        return self._command(request)
        
    def stop_task_by_name(self, task_name):
        """Stop a task by name."""
        self.stop_task(self.map_task_names()[task_name])

    def resume_task(self, uuid):
        """Resume a stopped task."""
        request = etree.Element("resume_task")
        request.set("task_id", uuid)
        return self._command(request)
        
    def resume_task_by_name(self, task_name):
        """Resume a task by name."""
        self.resume_task(self.map_task_names()[task_name])

    def delete_task(self, uuid):
        """Delete a task."""
        return self._delete("task", uuid=uuid)

    def list_results(self, **kwargs):
        """List task results."""
        return self._list("report", **kwargs)

    def get_result(self, uuid, **kwargs):
        """Get scan result by uuid."""
        return self._get('result', uuid=uuid)

    def list_reports(self, **kwargs):
        """List task reports."""
        return self._list("report", **kwargs)

    def get_report(self, uuid, **kwargs):
        """Get task report by uuid."""
        return self._get('report', uuid=uuid)

    def delete_report(self, uuid):
        """Delete a report."""
        return self._delete("report", uuid=uuid)

    def download_report(self, uuid, format_uuid=None, as_element_tree=False,
                        **kwargs):
        """Get XML or base64 encoded report contents"""
        request = etree.Element("get_reports")

        request.set("report_id", uuid)

        if format_uuid is not None:
            request.set("format_id", format_uuid)

        if kwargs is not {}:

            def filter_str(k, v):
                return "{}=\"{}\"".format(k, v)

            filters = [filter_str(k, v) for k, v in six.iteritems(kwargs) if v]

            if filters:
                request.set("filter", " ".join(filters))

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
        """List schedules and filter by kwargs."""
        return self._list("schedule", **kwargs)

    def create_schedule(self, name, comment=None, copy=None, first_time=None,
                        duration=None, duration_unit=None, period=None,
                        period_unit=None, timezone=None):
        """Create an OpenVAS task schedule"""

        data = {"name": name}

        if copy is not None:
            data["copy"] = copy

        if first_time is not None:
            data["first_time"] = first_time

        if duration is not None:
            data["duration"] = {
                "#text": duration,
                "unit": duration_unit
            }

        if period is not None:
            data["period"] = {
                "#text": period,
                "unit": period_unit
            }

        if comment is not None:
            data["comment"] = comment

        if timezone is not None:
            data["timezone"] = timezone

        request = dict_to_lxml("create_schedule", data)

        return self._create(request)

    def get_schedule(self, uuid, **kwargs):
        """Get schedule by uuid."""
        return self._get('schedule', uuid=uuid)

    def modify_schedule(self, uuid, **kwargs):
        """Modify schedule."""
        if 'duration' in kwargs:
            kwargs["duration"] = {
                "#text": kwargs.pop('duration'),
                "unit": kwargs.pop('duration_unit')
            }

        if 'period' in kwargs:
            kwargs["period"] = {
                "#text": kwargs.pop('period'),
                "unit": kwargs.pop('period_unit')
            }
        return self._modify('schedule', uuid=uuid, **kwargs)

    def delete_schedule(self, uuid):
        """Delete a schedule."""
        return self._delete('schedule', uuid=uuid)

    def list_nvts(self, details=False):
        """List NVTs including details."""
        if details:
            request = etree.Element('get_nvts', details='1')
        else:
            request = etree.Element('get_nvts')
        response = self._command(request)
        return response


    def get_nvt(self, uuid):
        """Returns a single NVT using an @nvt_oid."""
        return self._get('nvt', uuid=uuid)

    def get_nvt_family(self, uuid):
        """Return the id of the family that the NVT is a member of."""
        map = self.map_nvts()
        for family in map.keys():
            if uuid in family.keys():
                return family

    def list_nvt_families(self):
        """List NVT families."""
        request = etree.Element("get_nvt_families")
        response = self._command(request, cb=None)
        return response['families']['family']
    
    def map_nvts(self):
        """Return a dictionary mapping NVT families to lists of the 
        NVTs that they contain."""
        families = {}
        nvts = self.list_nvts(details=True)
        for nvt in nvts.data['nvt']:
            if nvt['family'] in families.keys():
                families[nvt['family']] += [{'oid':nvt['@oid'], 'name':nvt['name']}]
            else:
                families[nvt['family']] = [{'oid':nvt['@oid'], 'name':nvt['name']}]
        return families
    
    def map_nvts_to_families(self):
        """Return a dictionary mapping NVTs to the families they belong to"""
        # find the family of the NVT
        families = self.map_nvts()
        
        # reverse the mapping 
        oid_to_fam = {}
        for f in families.keys():
            for n in families[f]:
                oid_to_fam[n["oid"]] = f
        return oid_to_fam
    
    def _command(self, request, cb=None):
        """Send, build and validate response."""
        resp = self._send_request(request)

        response = Response(req=request, resp=resp, cb=cb)
        # validate response, raise exceptions, if any
        response.raise_for_status()

        return response

    def _get(self, data_type, uuid, cb=None):
        """Generic get function."""
        # deal with the non-standard plural
        if data_type == 'nvt_family':
            data_type = 'nvt_familie' 
        request = etree.Element("get_{}s".format(data_type))

        request.set("{}_id".format(data_type), uuid)

        if cb is None:
            def cb(resp):
                return list(
                    lxml_to_dict(resp.find(data_type)).values()
                )[0]

        return self._command(request, cb)

    def _map(self, data_type):
        """Generic function to map names to ids"""
        if data_type == 'nvt_family':
            data_type = 'nvt_familie' 
        List = self._list(data_type)
        Map = {}
        if data_type in ['nvt', 'preference']:
            for Item in List:
                Map[Item["name"]] = Item["@oid"]
        else:
            for Item in List:
                Map[Item["name"]] = Item["@id"]
        return Map

    def _list(self, data_type, cb=None, **kwargs):
        """Generic list function."""
        if data_type == 'nvt_family':
            data_type = 'nvt_familie' 
        request = etree.Element("get_{}s".format(data_type))

        if kwargs is not {}:
            def filter_str(k, v):
                return "{}=\"{}\"".format(k, v)
            filters = [filter_str(k, v) for k, v in six.iteritems(kwargs) if v]
            if filters:
                request.set("filter", " ".join(filters))

        if cb is None:
            def cb(resp):
                return [lxml_to_dict(i, True) for i in resp.findall(data_type)]

        response = self._command(request, cb=cb)

        return response

    def _create(self, request):
        """generic create function."""
        return self._command(request)

    def _modify(self, data_type, uuid, **kwargs):
        """Generic modify function."""
        request = dict_to_lxml("modify_{}".format(data_type), kwargs)

        request.set('{}_id'.format(data_type), uuid)

        return self._command(request)

    def _delete(self, data_type, uuid, cb=None):
        """Generic delete function."""
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
