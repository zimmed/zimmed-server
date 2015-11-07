"""Server exception classes.

.. moduleauthor:: Dave Zimmelman <zimmed@zimmed.io>

"""

from tornado.escape import json_encode


class HTTPError(Exception):
    STATUS = 0
    TITLE = ""
    STANDARD = "HTTP/1.1"

    def __init__(self, message, **kwargs):
        self.type = 'undefined'
        self.status = kwargs.get('status', self.__class__.STATUS)
        self.title = kwargs.get('title', self.__class__.TITLE)
        self.description = kwargs.get('description', message)
        self.standard = kwargs.get('standard', self.__class__.STANDARD)
        self.data = kwargs.get('data', None)
        super(HTTPError, self).__init__(message)

    # noinspection PyTypeChecker
    @property
    def header(self):
        return self.standard + ' ' + str(self.status) + ': ' + self.title

    def json(self):
        obj = {
            'status': self.status,
            'title': self.title,
            'description': self.description,
            'standard': self.standard,
            'header': self.header,
            'data': self.data
        }
        if self.type:
            obj['type'] = self.type
        return json_encode(obj)


class HTTPSuccess(HTTPError):
    STATUS = 200
    TITLE = "OK"

    def __init__(self, data=None):
        super(HTTPSuccess, self).__init__("Request succeeded.", data=data)


class BadRequestError(HTTPError):
    STATUS = 400
    TITLE = "Bad Request"


class UnauthorizedError(HTTPError):
    STATUS = 401
    TITLE = "Unauthorized"


class ForbiddenError(HTTPError):
    STATUS = 403
    TITLE = "Forbidden"


class NotFoundError(HTTPError):
    STATUS = 404
    TITLE = "Not Found"


class TimeOutError(HTTPError):
    STATUS = 408
    TITLE = "Request Timeout"


class TokenInvalidError(UnauthorizedError):
    STATUS = 498
    TITLE = "Token Expired/Invalid"
    STANDARD = "Esri"

