# -*- coding: utf-8 -*-


class Error(Exception):
    """Base Error Class"""

    def __str__(self):
        return repr(self)


class _ResponseError(Error):
    """OMP response error"""
    def __init__(self, cmd, *args):
        if cmd.endswith('_response'):
            cmd = cmd[:-9]
        super(_ResponseError, self).__init__(cmd, *args)

    def __str__(self):
        return '[Http {1}] {0}: {2}'.format(*self.args)


class ClientError(_ResponseError):
    """Command failed due to client"""


class ServerError(_ResponseError):
    """Command failed due to openvas manager"""


class ResultError(Error):
    """Invalid response from Server"""

    def __str__(self):
        return 'Invalid result: response from %s is invalid: %s' % self.args


class AuthenticationError(Error):
    """Authentication Failed"""
