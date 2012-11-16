import re
import hashlib
import hmac
import urlparse
import urllib2
import httplib
import mimetypes
from datetime import datetime, timedelta
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers


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
        print self.api
        request = urllib2.Request(self.api, datagen, headers)
        response = urllib2.urlopen(request)
        return json.loads(response.read())

    def create_assembly(self, files=None, fields=None, **params):
        if fields is None:
            fields = {}
        fields.update(get_fields(self.key, self.secret, params))
        return self._send_request(files, **fields)

    def get_assembly_result(self, assembly_id):
        assembly_url = '{}/{}'.format(self.api, assembly_id)
        return json.loads(urllib2.urlopen(assembly_url).read())


class TestClient(object):
    """
    Fake client for unit/functional tests. Reads directly responses from fixtures files.
    """
    def __init__(self, key, secret, api=None, media_root=None):
        self.api = api
        self.media_root = media_root

    def _get_response(self, url):
        response_content = urllib2.urlopen(url).read()
        response_content = re.sub('\{\{ TRANSLOADIT_API \}\}', self.api, response_content)
        response_content = re.sub('\{\{ MEDIA_ROOT \}\}', self.media_root, response_content)
        return json.loads(response_content)

    def create_assembly(self, files=None, fields=None, **params):
        url = u'{}/{}.json'.format(self.api, fields['type'])
        return self._get_response(url)

    def get_assembly_result(self, assembly_id):
        url = '{}/{}.json'.format(self.api, assembly_id)
        return self._get_response(url)
