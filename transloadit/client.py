from builtins import object
import hashlib
import hmac
import json
import re
import requests

from datetime import datetime, timedelta

ASSEMBLY_API_URL = 'http://api2.transloadit.com/assemblies'


def sign_request(secret, params):
    return hmac.new(secret.encode(), json.dumps(params).encode(), hashlib.sha1).hexdigest()


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
    def __init__(self, key, secret, api=None, timeout=5):
        self.key = key
        self.secret = secret
        self.timeout = timeout
        if api:
            self.api = api
        else:
            self.api = ASSEMBLY_API_URL

    def request(self, files=None, **params):

        response = requests.post(ASSEMBLY_API_URL, data=params,
                                 files=files, timeout=self.timeout)

        return response.json()

    def create_assembly(self, files=None, fields=None, **params):
        if fields is None:
            fields = {}
        fields.update(get_fields(self.key, self.secret, params))
        return self.request(files, **fields)

    def get_assembly_result(self, assembly_id):
        assembly_url = '{}/{}'.format(self.api, assembly_id)
        return requests.get(assembly_url, timeout=self.timeout).json()



class TestClient(object):
    """
    Fake client for unit/functional tests. Reads directly responses from fixtures files.
    """
    def __init__(self, key, secret, api=None, media_root=None, timeout=5):
        self.api = api
        self.media_root = media_root
        self.timeout = timeout

    def _get_response(self, url):
        file_path = url.replace("file://", "")
        with open(file_path) as json_file:
            content = json_file.read()
            content = re.sub(r'{{ TRANSLOADIT_API }}', self.api, content)
            content = re.sub(r'{{ MEDIA_ROOT }}', self.media_root, content)
            return json.loads(content)

    def create_assembly(self, files=None, fields=None, **params):
        url = u'{}/{}.json'.format(self.api, fields['type'])
        return self._get_response(url)

    def get_assembly_result(self, assembly_id):
        url = '{}/{}.json'.format(self.api, assembly_id)
        return self._get_response(url)

