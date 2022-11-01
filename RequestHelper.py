"""
Created on Apr 21, 2022

@author: arno

Request URL Helper to get response from API 
"""
import time
from typing import Dict

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class RequestHelper():
    """
    Functions to help requesting response from an API
    """

    def __init__(self):
        self.session = self._init_session()

    @staticmethod
    def _init_session():
        """
        Initialization of the session 
        """
        session = requests.Session()
        #session.headers.update({'Accept': 'application/json'})
        retry = Retry(total=5, backoff_factor=1.5,
                      respect_retry_after_header=True,
                      status_forcelist=[502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def update_header(self, params: dict):
        """Update the header of the session 

        params = dictionary with parameters for the header
        """
        self.session.headers.update(params)

    def get_request_response(self, url, stream=False) -> dict:
        """general request url function 

        should be a class, with _init etc

        url = api url for request
        download_file = request is for downloading a file
                       (no convertion to json)
        """

        # debug info
        #print('Inside RequestHelper.getRequestResponse')
        #print('URL: ', url)

        resp = {}
        response = requests.Response
        request_timeout = 120

        try:
            while True:
                response = self.session.get(
                    url, timeout=request_timeout, stream=stream, verify=True)
                if response.status_code == 429:
                    if 'Retry-After' in response.headers.keys():
                        sleep_time = int(response.headers['Retry-After'])+1
                        self.sleep_print_time(sleep_time)
                    else:
                        raise requests.exceptions.RequestException
                else:
                    break
        except requests.exceptions.RequestException:
            print('Header request exception:', response.headers)
            print(response.text)
            raise
        except Exception:
            print('Exception:', response.headers)
            print(response.text)
            raise

        try:
            # get json from response, with type dict (mostly) or type list (Alcor exchange)
            resp_unknown = response.json()

            # when return type is a list, convert to dict
            if isinstance(resp_unknown, list):
                resp.update({'result': resp_unknown})
            else:
                resp = resp_unknown

        except Exception as e:
            print('JSON Exception: ', e)

        try:
            response.raise_for_status()
            resp.update({'status_code': response.status_code})

        except requests.exceptions.HTTPError as e:
            print('No status Exception: ', e)

            # check if error key is in result dictionary
            if 'error' in resp:
                resp.update({'status_code': 'error'})
            else:
                resp.update({'status_code': 'no status'})

        except Exception as e:
            print('Other Exception: ', e)  # , response.json())
            # raise
            resp.update({'status_code': 'error'})
            resp.update({'prices': []})

        return resp

    def api_url_params(self, url, params: dict, api_url_has_params=False):
        """
        Add params to the url

        url = url to be extended with parameters
        params = dictionary of parameters
        api_url_has_params = bool to extend url with '?' or '&'
        """
        if params:
            # if api_url contains already params and there is already a '?' avoid
            # adding second '?' (api_url += '&' if '?' in api_url else '?'); causes
            # issues with request parametes (usually for endpoints with required
            # arguments passed as parameters)
            url += '&' if api_url_has_params else '?'
            for key, value in params.items():
                if type(value) == bool:
                    value = str(value).lower()

                url += '{0}={1}&'.format(key, value)
            url = url[:-1]
        return url

    def sleep_print_time(self, sleeping_time):
        """
        Sleep and print countdown timer
        Used for a 429 response retry-after

        sleeping_time = total time to sleep in seconds
        """
        print()
        print('Retrying in %s s' % (sleeping_time))
        for i in range(sleeping_time, 0, -1):
            print('\r{:3d} seconds remaining.'.format(i), end='', flush=True)
            time.sleep(1)
        print()


def __main__():
    pass


if __name__ == '__main__':
    __main__()
