import hashlib
import hmac
import urlparse
import httplib
import mimetypes
from datetime import datetime, timedelta
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
import urllib2


register_openers()

try:
    from django.utils import simplejson as json
except ImportError:
    import simplejson as json


BASE_API = 'http://api2.transloadit.com/assemblies'
FILE_BOUNDARY = '----------Python_Transloadit_Client_Boundary_$'
CRLF = '\r\n'


def sign_request(secret, params):
    return hmac.new(secret, json.dumps(params),
        hashlib.sha1).hexdigest()


def get_fields(key, secret, params):

    if 'auth' not in params:
        params['auth'] = {
            'key': key,
            'expires': (datetime.now() + timedelta(days=1)).strftime('%Y/%m/%d %H:%M:%S')
        }

        return {
            'params': json.dumps(params),
            'signature': sign_request(secret, params)
        }


class Client(object):
    def __init__(self, key, secret, api=None):
        self.key = key
        self.secret = secret
        if api:
            self.api = api
        else:
            self.api = BASE_API

    def _sign_request(self, params):
        return hmac.new(self.secret, json.dumps(params),
            hashlib.sha1).hexdigest()

    def _send_request(self, files, **fields):
        parts = urlparse.urlparse(self.api)
        if files:
            for index, file_ in enumerate(files):
                fields['file{}'.format(index+1)] = open(file_, mode='rb')
        datagen, headers = multipart_encode(fields)
        request = urllib2.Request(self.api, datagen, headers)
        response = urllib2.urlopen(request)
        return json.loads(response.read())

    def request(self, files=None, fields=None, **params):
        if fields is None:
            fields = {}

        fields.update(get_fields(self.key, self.secret, params))

        return self._send_request(files, **fields)
