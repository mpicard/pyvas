#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
openvas.omplib.cmd - An OMP (OpenVAS Management Protocol) command line client.
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

from __future__ import with_statement

__author__ = "Hartmut Goebel <h.goebel@goebel-consult.de>"
__copyright__ = "Copyright 2010 by Hartmut Goebel <h.goebel@goebel-consult.de>"
__licence__ = "GNU General Public License version 3 (GPL v3)"

from openvas.omplib import *
from openvas.omplib import  __version__
# use the same etree implementations as omplib
from openvas.omplib import etree

import inspect
import sys
import time
import argparse
import string
import textwrap

try:
    from gettext import gettext
except ImportError:
    def gettext(message):
        return message
_ = gettext


class OMPCommandClient(object):
    def __init__(self, args):
        self.client = OMPClient(args.host, args.port,
                                args.username, args.password)

    def run_command(self, optparser, args):
        mod = inspect.getmodule(self)
        cmd = getattr(mod, args.command_name.replace('-', '_'))
        self.client.open()
        try:
            res = cmd.run(self.client, args)
        except Error, e:
            sys.exit('Error: %s' % e)
        finally:
            self.client.close()
        return res
        
    @classmethod
    def _find_commands(klass):
        def is_OMPCommand(c):
            return inspect.isclass(c) and OMPCommand in c.__bases__
        
        classes = inspect.getmembers(inspect.getmodule(klass), is_OMPCommand)
        return (c[1] for c in classes)


class OMPCommand(object):
    @classmethod
    def _argparse(klass, subparsers):
        cmd_name = klass.__name__.replace('_', '-')
        description = klass.__doc__.rstrip()
        help = description.lstrip().split('\n', 1)[0]
        description = textwrap.dedent(description)
        sp = subparsers.add_parser(cmd_name,
                                   formatter_class=argparse.RawDescriptionHelpFormatter,
                                   help=help,
                                   description=description)
        klass._add_arguments(sp)


class create_task(OMPCommand):
    """Create a task"""
    
    @staticmethod
    def _add_arguments(sp):
        sp.add_argument('-n', '--name', default="unnamed task",
                        help="Name for the new task")
        sp.add_argument('-m', '--comment', default="",
                        help="Comment for the new task ",
                        metavar='TEXT')
        #sp.add_argument('-r', '--rc',
        #                help="Create task with RC read from stdin")
        sp.add_argument('-c', '--config',
                        default=DEFAULT_CONFIG,
                        help=("Name of config to use for this task"
                              " (default: %(default)r)"),
                        metavar='NAME')
        sp.add_argument('-t', '--target',
                        default=DEFAULT_TARGET,
                        help=("Name of target to use for this task"
                              " (default: %(default)r)"),
                        metavar='NAME')

    @staticmethod
    def run(omp_client, args):
        print omp_client.create_task(name=args.name, comment=args.comment,
                                     config=args.config, target=args.target)


class delete_task(OMPCommand):
    """Delete one or more tasks"""
    
    @staticmethod
    def _add_arguments(sp):
        sp.add_argument('uuid', nargs='+', help='Uuids for tasks to delete')

    @staticmethod
    def run(omp_client, args):
        for uuid in args.uuid:
            omp_client.delete_task(uuid)


class delete_report(OMPCommand):
    """Delete one or more reports"""
    
    @staticmethod
    def _add_arguments(sp):
        sp.add_argument('uuid', nargs='+', help='Uuids for reports to delete')

    @staticmethod
    def run(omp_client, args):
        for uuid in args.uuid:
            omp_client.delete_report(uuid)


class get_report(OMPCommand):
    """Get report of one task"""
    
    @staticmethod
    def _add_arguments(sp):
        sp.add_argument('uuid', nargs='+', help='Uuids for reports to fetch')
        sp.add_argument('-f', '--format',
                        help="Report format (default: %(default)s).",
                        choices=[f.lower() for f in REPORT_FORMATS],
                        default=REPORT_FORMAT_XML.lower(),
                        type=string.lower)
        sp.add_argument('-o', '--output-file',
                        help=("This specifies the output filename to write to "
                              "or standard output by default"),
                        metavar='FILENAME'
                        )
        sp.add_argument('--search',
                        help="List only results containing this phrase",
                        dest='search_phrase', # name used in OPM command
                        metavar='PHRASE')
        sp.add_argument('--levels', default='',
                        help=("List only results matching one of these "
                              "levels. "
                              "Concat single characters of levels "
                              "(h: high, m: medium, l:log, g: log, d: debug) "
                              "like 'ml'. Default: all levels. "
                              "NB: This option may change soon."))
        sp.add_argument('--first-result', default=0, type=int,
                        help="First result to fetch",
                        metavar='NUM'
                        )
        sp.add_argument('--num-results', default=-1, type=int,
                        help=("Fetch at maximum NUM results "
                              "('-1' means no limit; default: no limit)"),
                        metavar='NUM'
                        )

        sp.add_argument('--sort-field',
                        help=("Sort results by this field (default: "
                              "%(default)s; service = ports, "
                              "level = thread level)"),
                        choices=('service', 'level'),
                        default='level',
                        type=string.lower)
        sp.add_argument('--sort-order', choices=['ascending', 'descending'],
                        default='descending',
                        type=string.lower)

        sp.add_argument('--notes', action='store_true',
                        help="Include notes in report")
        sp.add_argument('--notes-details', action='store_true',
                        help=("Include notes details in report "
                              "(requires --notes to be given, too)"))

    @staticmethod
    def run(omp_client, args):
        # map command line names of `sort-field` to internal names
        args.sort_field = {'level': 'type', 'service': 'port'}[args.sort_field]
        for uuid in args.uuid:
            res = omp_client.get_report(uuid, format=args.format.upper(),
                search_phrase=args.search_phrase, levels=args.levels,
                first_result=args.first_result, max_results=args.num_results,
                sort_field=args.sort_field, sort_order=args.sort_order,
                notes=args.notes, notes_details=args.notes_details,
                )

            if args.format == REPORT_FORMAT_XML:
                res = etree.tostring(res)
            if args.output_file is not None:
                try:
                    with open(args.output_file, 'wb') as out:
                        out.write(res)
                except IOError, e:
                    sys.exit(str(e))
            else:
                sys.stdout.write(res)


class get_status(OMPCommand):
    """
    Get status of one, many or all tasks.
    
    If any uuid is given, the output includes a list of all reports
    for the requested tasks. If no uuid is given, only the first,
    second last and last report is listed (without duplicates). The
    list of reports is indented below the respective task. Each line
    conists of the report-uuid, number of holes, warnings, infos and
    log and the timestamp.
    """
    
    @staticmethod
    def _add_arguments(sp):
        sp.add_argument('uuid', nargs='*',
                        help='Uuids of tasks to get status for')
        
    @staticmethod
    def run(omp_client, args):

        def print_report(report):
            print "  %(id)s  " % report,
            print "%(hole)3s %(warning)3s %(info)3s %(log)3s" % report['messages'],
            try:
                timestamp = time.strptime(report['timestamp'])
                print time.strftime(" %Y-%m-%d %H:%M:%S", timestamp)
            except:
                # failed to parse time format, dump what we got
                print " %(timestamp)s" % report

        def print_task(task):
            if not first:
                print
            if task['status'] == 'Running':
                print ('%(id)s\t%(status)s %(progress)s%%\t%(name)s' % task)
            else:
                print ('%(id)s\t%(status)s\t%(name)s' % task)
            # Print any reports indented under the task.
            printed = set()
            if task.get('reports', None):
                for report in task['reports']:
                    print_report(report)
            else:
                for report in ('first', 'second_last', 'last'):
                    # second_lst may be the same as first, thus we need to track
                    report = task.get(report+'_report', None)
                    if report and not report['id'] in printed:
                        print_report(report)
                        printed.add(report['id'])
          
        first = True
        if args.uuid:
            for uuid in args.uuid:
                task = omp_client.get_task_status(uuid)
                print_task(task)
                first = False
        else:
            for task in omp_client.get_task_status():
                print_task(task)
                first = False


class start_task(OMPCommand):
    "Start one or more tasks"
    
    @staticmethod
    def _add_arguments(sp):
        sp.add_argument('uuid', nargs='+', help='Uuids of tasks to start')

    @staticmethod
    def run(omp_client, args):
        for uuid in args.uuid:
            omp_client.start_task(uuid)


class modify_task(OMPCommand):
    "Modify a task"
    
    @staticmethod
    def _add_arguments(sp):
        sp.add_argument('uuid', nargs=1, help='Uuid of task to modify')

    @staticmethod
    def run(omp_client, args):
        raise NotImplementedError
        omp_client.modify_task(args[0], args.name, args.file)


class help(OMPCommand):
    "Get help message from OMP server"
    
    @staticmethod
    def _add_arguments(sp): pass

    @staticmethod
    def run(omp_client, args):
        res = omp_client.help()
        print res.strip('\n')


class xml(OMPCommand):
    "Send plain XML command"
    
    @staticmethod
    def _add_arguments(sp):
        sp.add_argument('xml', nargs=1, help='XML text/document to send')

    @staticmethod
    def run(omp_client, args):
        res = omp_client.xml(args.xml[0], xml_result=True)
        print etree.tostring(res)


def run():
    import argparse
    import getpass
    
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--help", action="help",
                        help=_("show this help message and exit"))
    parser.add_argument("--version", action='version', version=__version__)
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Verbose messages.")
    parser.add_argument('-P', '--prompt', action='store_true',
                        help="Prompt to exit.")

    group = parser.add_argument_group('Options for connecting to the manager')
    group.add_argument('-h', '--host', default=MANAGER_ADDRESS,
                       help=("Connect to manager on host HOST "
                             "(default: %(default)s)"))
    group.add_argument('-p', '--port', type=int, default=MANAGER_PORT,
                       help="Use port number PORT (default: %(default)s)")
    group.add_argument('-u', '--username', default=getpass.getuser(),
                       help="OMP username (default: current user's name)")
    group.add_argument('-w', '--password',
                       help="OMP password (default: same as username)")

    subparsers = parser.add_subparsers(dest='command_name',
                                       title='Available OMP commands',
                                       help='Get help for sub-commands with <cmd> --help')

    for cmd in OMPCommandClient._find_commands():
        cmd._argparse(subparsers)

    args = parser.parse_args()
    
    if not (0 < args.port < 65536):
        parser.error('Manager port must be a number between 1 and 65535.')
    if args.password is None:
        args.password = args.username

    client = OMPCommandClient(args)
    client.run_command(parser, args)

if __name__ == '__main__':
    run()
