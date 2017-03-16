#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
openvas.omplib - An OMP (OpenVAS Management Protocol) client interface for Python.

Results from OMP methods
---------------------------

In general all OMPClient methods return either a utf-8 encoded string
or an etree Element. If errors occur an exception subclassed from
`openvas.omplib.Error` is raised.

Changing the ElementTree library
------------------------------------

``openvas.omplib`` per default uses xml.etree.ElementTree (resp. it's
C-implementation xml.etree.cElementTree if available). If your
application is using another ElementTree library (e.g. lxml) you can
easily make openvas.omplib using it by monkey-pathing openvas.omplib::

  # at the very beginning of your application
  from lxml import etree
  import openvas.omplib
  openvas.omplib.etree = etree
  # need to comply to the ElementTree 1.2 interface
  etree.XMLTreeBuilder = etree.XMLParser

You may want to run the test suite to ensure it is really wroking,
though.
"""
#
# Copyright 2010 by Hartmut Goebel <h.goebel@goebel-consult.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

__author__ = "Hartmut Goebel <h.goebel@goebel-consult.de>"
__copyright__ = "Copyright 2010 by Hartmut Goebel <h.goebel@goebel-consult.de>"
__licence__ = "GNU General Public License version 3 (GPL v3)"
__version__ = "0.1.0"

import socket
import ssl

try:
    from xml.etree import cElementTree as etree
except ImportError:
    from xml.etree import ElementTree as etree


MANAGER_ADDRESS = '127.0.0.1'
MANAGER_PORT = 9390

DEFAULT_CONFIG = "Full and fast"
DEFAULT_TARGET = "Localhost"

REPORT_FORMAT_PDF  = 'PDF'
REPORT_FORMAT_HTML = 'HTML'
REPORT_FORMAT_XML  = 'XML'
REPORT_FORMAT_ITG  = 'ITG'
REPORT_FORMAT_CPE  = 'CPE'
REPORT_FORMAT_NBE  = 'NBE'

REPORT_FORMATS = (REPORT_FORMAT_XML, REPORT_FORMAT_PDF, REPORT_FORMAT_HTML,
                  REPORT_FORMAT_ITG, REPORT_FORMAT_CPE, REPORT_FORMAT_NBE)

class Error(Exception):
    """Base class for OMP errors."""
    def __str__(self):
        return repr(self)

class _ErrorResponse(Error):
    def __init__(self, cmd, *args):
        if cmd.endswith('_response'):
            cmd = cmd[:-9]
        super(_ErrorResponse, self).__init__(cmd, *args)
        
    def __str__(self):
        return '%s %s' % self.args[1:3]

class ClientError(_ErrorResponse):
    """command issued could not be executed due to error made by the client"""
    
class ServerError(_ErrorResponse):
    """error occurred in the manager during the processing of this command"""
    
class ResultError(Error):
    """Get invalid answer from Server"""
    def __str__(self):
        return 'Result Error: answer from command %s is invalid' % self.args

class AuthFailedError(Error):
    """Authentication failed."""


def XMLNode(tag, *kids, **attrs):
    n = etree.Element(tag, attrs)
    for k in kids:
        if isinstance(k, basestring):
            assert n.text is None
            n.text = k
        else:
            n.append(k)
    return n


class OMPClient(object):
    def __init__(self, host, port=MANAGER_PORT, username=None, password=None):
        self.socket = None
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.session = None

    def open(self, username=None, password=None):
        """Open a connection to the manager and authenticate the user."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket = sock = ssl.wrap_socket(sock)
        sock.connect((self.host, self.port))
        self.authenticate(username, password)

    def close(self):
        """Close the connection to the manager"""
        self.socket.close()
        self.socket = None

    def _send(self, data):
        """Send OMP data to the manager and read the result.

        `data` may be either an unicode string, an utf-8 encoded
        string or an etree Element. The result is as an etree Element.
        """
        BLOCK_SIZE = 1024
        if etree.iselement(data):
            #print '>>>', etree.tostring(data)
            root = etree.ElementTree(data)
            root.write(self.socket, 'utf-8')
        else:
            if isinstance(data, unicode):
                data = data.encode('utf-8')
            self.socket.send(data)
        parser = etree.XMLTreeBuilder()
        while 1:
            res = self.socket.recv(BLOCK_SIZE)
            #print repr(res)
            parser.feed(res)
            if len(res) < BLOCK_SIZE:
                break
        root = parser.close()
        #print '<<<', etree.tostring(root)
        return root

    def _check_response(self, response):
        """Check the response read from the manager.

        If the response status is 4xx a ClientError is raised, if the
        status is 5xx a ServerError is raised.
        """
        status = response.get('status')
        if status is None:
            raise RunTimeError('response is missing status: %s'
                               % etree.tostring(response))
        if status.startswith('4'):
            raise ClientError(response.tag, status,
                              response.get('status_text'))
        elif status.startswith('5'):
            raise ServerError(response.tag, status,
                              response.get('status_text'))
        return status

    def _text_command(self, request):
        response = self._send(request)
        self._check_response(response)
        return response.text

    def _xml_command(self, request):
        response = self._send(request)
        self._check_response(response)
        return response

    def _create_command(self, request, id_tag):
        response = self._xml_command(request)
        try:
            uuid = response.find(id_tag).text
        except:
            raise ResultError(response.tag)
        return uuid

    def __generic_get(self, type, name, element2dict):
        """
        Generic function for retrieving information using <get_XXX>.

        If 'name' is not given, retrieve all thingies. Result is a
        generator of dicts with the thingies datas.
        
        If 'name' is set, get only the thingy identified by its name.
        Result is a single dict with the thingies data.
        """
        request = XMLNode('get_%s' % type)
        if name is not None:
            request.set('name', name)
        response = self._xml_command(request)
        if name:
            return element2dict(response[0])
        else:
            return (element2dict(elem) for elem in response)


    def __generic_delete(self, type, name=None, id=None):
        """
        Generic function for deleting thingies using <delete_XXX>.
        """
        request = XMLNode('delete_%s' % type)
        if id is not None:
            request.set('id', id)
        if name is not None:
            n = XMLNode('name', name)
            request.append(n)
        return self._text_command(request)


    # --- basic commands ---

    def authenticate(self, username=None, password=None):
        """
        Authenticate a user to the manager.

        If username or password are not gives, the values passed when
        instanciating the object are used.

        Raises AuthFailedError if authentication failed due to wrong
        credentials.
        """
        if username is None:
            username = self.username
        if password is None:
            password = self.password
        request = XMLNode("authenticate",
                          XMLNode("credentials",
                                  XMLNode("username", username),
                                  XMLNode("password", password),
                                  ))
        try:
            self._text_command(request)
            # if not status: connection closed, raise error
        except ClientError:
            raise AuthFailedError(username)

    def help(self):
        """
        Retrieve help from OMP server.
        """
        return self._text_command(XMLNode('help'))

    def xml(self, xmldata, xml_result=False):
        """Low-level interface to send OMP XML to the manager.

        `xmldata` may be either a utf-8 encoded string or an etree
        Element. If `xml_result` is true, the result is returned as an
        etree Element, otherwise a utf-8 encoded string is returned.

        Please see the modules documentation about how to change the
        ElementTree library used.
        """
         
        if xml_result:
            return self._xml_command(xmldata)
        else:
            return self._text_command(xmldata)

    # --- agents ---

    def create_agent(self, name, installerdata, comment='',
                     howto_use='', howto_install=''):
        """
        Create an agent.
        """
        installerdata = installerdata.encode('base64')
        # error message: CREATE_AGENT installer must be at least one byte long
        request = XMLNode("create_agent",
                          XMLNode("name", name),
                          XMLNode("comment", comment),
                          XMLNode("installer", installerdata),
                          XMLNode("howto_use", howto_use),
                          XMLNode("howto_install", howto_install)
                          )
        self._text_command(request)

    def get_agents(self, name=None):
        """
        Get information about agent(s).

        If 'name' is not given, retrieve all agents. Result is a
        generator of dicts with the agenta datas.
        
        If 'name' is set, get only the agent identified by its name.
        Result is a single dict with the agenta data.
        """

        def agent2dict(element):
            entry = dict((elem.tag, elem.text) for elem in element)
            return entry

        return self.__generic_get('agents', name, agent2dict)


    def delete_agent(self, name):
        """Delete an agent identified by it's name."""
        self.__generic_delete('agent', name=name)


    # --- configs ---

    def create_config(self, name, rcdata, comment=''):
        """
        Create a config, given the config description as a string.
        """
        raise NotImplementedError
        rcdata = rcdata.encode('base64')
        request = XMLNode("create_config",
                          XMLNode("name", name),
                          XMLNode("comment", comment),
                          XMLNode("rcfile", rcdata),
                          )
        return self._create_command(request, 'config_id')


    def get_configs(self, name=None):
        """
        Get information about config(s).

        If 'name' is not given, retrieve all configs. Result is a
        generator of dicts with the config datas.
        
        If 'name' is set, get only the config identified by its name.
        Result is a single dict with the config data.
        """

        def config2dict(element):
            entry = dict((elem.tag, elem.text) for elem in element)
            entry['tasks'] = [(elem.get('id'), elem.find('name').text)
                              for elem in element.find('tasks')]
            return entry

        return self.__generic_get('configs', name, config2dict)


    def delete_config(self, name):
        """Delete a config identified by it's name"""
        self.__generic_delete('config', name=name)


    # --- escalators ---

    def create_escalator(self, name, *args, **kwargs):
        """Create an escalator."""
        """
        <create_escalator>
        <name>unnamed-33</name>
        <comment>hjhjklh</comment>
        <condition>Threat level at least<data><name>level</name>Medium</data></condition>
        <event>Task run status changed<data><name>status</name>Done</data></event>
        <method>Email<data><name>to_address</name>aaaa@example.com</data><data><name>from_address</name>vaaa@example.com</data><data><name>notice</name>1</data></method>
        </create_escalator>
        """
        raise NotImplementedError

    def get_escalators(self, name=None):
        """
        Get information about escalator(s).

        If 'name' is not given, retrieve all escalators. Result is a
        generator of dicts with the escalator datas.
        
        If 'name' is set, get only the escalator identified by its
        name. Result is a single dict with the escalator data.
        """

        def escalators2dict(element):
            entry = dict((elem.tag, elem.text) for elem in element)
            tasks = element.find('tasks')
            if tasks is None: tasks = []
            entry['tasks'] = [(elem.get('id'), elem.find('name').text)
                               for elem in tasks]
            return entry

        return self.__generic_get('escalators', name, escalators2dict)

    def delete_escalator(self, name):
        """Delete an escalator identified by it's name"""
        self.__generic_delete('escalator', name=name)


    def test_escalator(self, name):
        """Test an escalator."""
        request = XMLNode("test_escalator",
                          XMLNode("name", name),
                          )
        self._text_command(request)

    # --- lsc credentials ---

    def create_lsc_credential(self, name, login, comment=''):
        """Create an LSC Credential."""
        request = XMLNode("create_lsc_credential",
                          XMLNode("name", name),
                          XMLNode("login", login),
                          XMLNode("comment", comment),
                          )
        return self._create_command(request, 'lsc_credential_id')

    def get_lsc_credentials(self, name=None):
        """
        Get information about lsc_credential(s).

        If 'name' is not given, retrieve all lsc_credentials. Result
        is a generator of dicts with the lsc_credential datas.
        
        If 'name' is set, get only the lsc_credential identified by
        its name. Result is a single dict with the lsc_credential
        data.
        """

        def credentials2dict(element):
            entry = dict((elem.tag, elem.text) for elem in element)
            entry['targets'] = [(elem.get('id'), elem.find('name').text)
                                for elem in element.find('targets')]
            return entry

        return self.__generic_get('lsc_credentials', name, credentials2dict)


    def delete_lsc_credential(self, name):
        """Delete a LSC credential identified by it's name"""
        self.__generic_delete('lsc_credential', name=name)

    # --- notes ---
    # NotImplemented
    
    # --- targets ---

    def create_target(self, name, hosts, comment=''):
        """Create a target."""
        request = XMLNode("create_target",
                          XMLNode("name", name),
                          XMLNode("hosts", hosts),
                          XMLNode("comment", comment),
                          )
        # NB: does not return a uuid, but a name
        return self._text_command(request)

    def get_targets(self, name=None):
        """
        Get information about target(s).

        If 'name' is not given, retrieve all targets. Result is a
        generator of dicts with the target datas.
        
        If 'name' is set, get only the target identified by its name.
        Result is a single dict with the target data.
        """

        def target2dict(element):
            entry = dict((elem.tag, elem.text) for elem in element)
            entry['tasks'] = [(elem.get('id'), elem.find('name').text)
                             for elem in element.find('tasks')]
            entry['lsc_credential'] = [
                elem.text for elem in element.find('lsc_credential').find('name')]
            return entry

        return self.__generic_get('targets', name, target2dict)


    def delete_target(self, name):
        """Delete a target identified by it's name"""
        self.__generic_delete('target', name=name)

    # --- tasks ---

    def create_task(self, name, comment=None, rcdata=None,
                    config=None, target=None):
        """
        Create a task.
        """
        if rcdata:
            assert not config and not target
            rcdata = rcdata.encode('base64')
            request = XMLNode("create_task",
                              XMLNode("rcfile", rcdata),
                              XMLNode("name", name),
                              XMLNode("comment", comment),
                              )
        else:
            assert config and target
            request = XMLNode("create_task",
                              XMLNode("config", config),
                              XMLNode("target", target),
                              XMLNode("name", name),
                              XMLNode("comment", comment),
                              )
        return self._create_command(request, 'task_id')


    def get_task_status(self, task_id=None, xml_result=False):
        """
        Get information about task(s).

        If 'task_id' is not given, retrieve all tasks. Result is a
        generator of dicts with the tasks datas.
        
        If 'task_id' is set, get only the task identified by this
        uuid. Result is a single dict with the tasks data.

        If `xml_result` is true, etree Elements are returned instead
        of dicts.
        """
        def progress2dict(elem):
            return elem.text or elem[-1].tail
        def elem2list(elem):
            return [elem2dict(e) for e in elem]

        def elem2dict(element, specials=[]):
            entry = {}
            if element.get('id'):
                entry['id'] = element.get('id')
            for elem in element:
                if  elem.tag in specials:
                    entry[elem.tag] = specials[elem.tag](elem)
                elif len(elem) == 0:
                    entry[elem.tag] = elem.text
                elif len(elem) == 1 and elem[0].tag == 'name':
                    entry[elem.tag] = elem[0].text
                elif len(elem) == 1 and elem[0].tag == 'report':
                    entry[elem.tag] = elem2dict(elem[0])
                else:
                    entry[elem.tag] = elem2dict(elem)
            return entry

        request = XMLNode('get_status')
        if task_id:
            request.set('task_id', task_id)
        response = self._xml_command(request)
        tasks = response.findall('task')
        specials = {
            'progress': progress2dict,
            'reports': elem2list,
            }
        if xml_result:
            elem2dict = lambda a: a
        if task_id:
            return elem2dict(tasks[0], specials=specials)
        else:
            return (elem2dict(elem, specials=specials) for elem in tasks)


    def wait_for_task(self, wait_status, sleep_pause=1):
        """
        Wait for a task to start, end, being stopped or being deleted.

        This function polls the tasks status until the task reaches
        the status to wait for - or any 'higher' status.

        :`wait_status`: should be one of 'start', 'stop', 'done',
                        'delete'.
        :`sleep_pause`: pause `sleep_pause` seconds between polls.

        Returns `True` on success, `False` on internal error in task.
        """
        wait_status = wait_status.lower()
        while True:
            try:
                status = self.get_task_status(task_id).lower()
            except:
                if wait_status == 'delete':
                    return True
                else:
                    raise
            if status == 'internal error':
                return False
            elif status == 'done':
                # huh? reconsider for "start"
                return True
            elif status == 'stopped':
                return wait_status == 'stop'
            elif status == 'running' and wait_status == 'start':
                return True
            time.sleep(sleep_pause)
    

    def modify_task(self, **kw):
        """Modify a task."""
        raise NotImplementedError

    def start_task(self, task_id):
        """Start a tasks."""
        request = XMLNode('start_task', task_id=task_id)
        response = self._xml_command(request)
        try:
            report_uuid = response.find('report_id').text
        except:
            raise ResultError(response.tag)
        return report_uuid

    def abort_task(self, task_id):
        """Abort a task."""
        self._text_command(XMLNode('abort_task', task_id=task_id))

    def delete_task(self, task_id):
        """Delete a task identified by it's uuid."""
        self._text_command(XMLNode('delete_task', task_id=task_id))


    # --- reports ---

    def get_report(self, report_id, format=REPORT_FORMAT_XML,
                   first_result=0, max_results=-1,
                   sort_field=None, sort_order='descending',
                   levels='hmlgd', notes=True, notes_details=True,
                   search_phrase=None):
        """
        Get report of one task.

        If report format is XML, the result will be a XML element
        tree. Otherwise it will be a (byte) string.
        """
        # todo: validate sort_order
        request = XMLNode('get_report',
                          report_id=report_id,
                          first_result=str(first_result),
                          max_results=str(max_results),
                          sort_field=sort_field or '' ,
                          sort_order=sort_order,
                          levels=levels,
                          format=format or REPORT_FORMAT_XML,
                          notes=notes and '1' or '0',
                          notes_details=notes_details and '1' or '0',
                          search_phrase=search_phrase or ''
                          )
        response = self._xml_command(request)
        report = response.find('report')
        if format != REPORT_FORMAT_XML:
            report = report.text.decode('base64')
        return report

    def delete_report(self, report_id):
        """Delete a report identified by it's uuid."""
        self._text_command(XMLNode('delete_report', report_id=report_id))


    # --- misc ---

    def get_preferences(self, wait=False):
        """Get the manager preferences."""
        if wait:
            raise NotImplementedError
            return self.response_503("<get_preferences/>")
        response = self._xml_command(XMLNode('get_preferences'))
        prefs = dict((elem.find('name').text, elem.find('value').text)
                     for elem in response)
        return prefs

    def get_certificates(self):
        """Get the manager certificates."""
        #raise NotImplementedError
        response = self._xml_command(XMLNode('get_certificates'))
        return etree.tostring(response)
        
    
    def _until_up(self, method):
        raise NotImplementedError
    
    def get_nvt_details(self, oid=None):
        """Get NVT Information."""
        request = XMLnode('et_nvt_details')
        if oid is not None:
            request.set('oid', oid)
        return self.response_503(request)

#omp_response_503
#get_nvt_all
#get_nvt_feed_checksum
#get_rules_503
#get_dependencies_503
#wait_for_task_start
#wait_for_task_end
#wait_for_task_stop
#wait_for_task_delete
