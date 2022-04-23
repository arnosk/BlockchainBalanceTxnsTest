'''
Created on Apr 21, 2022

@author: arno

Request URL Helper to get response from API 
'''
import sys
import time
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

class RequestHelper():
    '''
    Functions to help requesting response from an API
    '''

    def __init__(self):
        self.session = self._init_session()

    @staticmethod
    def _init_session():       
        session = requests.Session()
        session.headers.update({'Accept': 'application/json'})
        retries = Retry(total=5, backoff_factor=0.5, status_forcelist=[502, 503, 504])
        session.mount('http://', HTTPAdapter(max_retries=retries))
        return session


    def updateHeader(self, dict:{}):
        self.session.headers.update(dict)
        

    def getRequestResponse(self, url, downloadFile = False):
        '''
        general request url function 
        should be a class, with _init etc
        '''
        resp = []
        request_timeout = 120

        try:
            while True:
                response = self.session.get(url, timeout=request_timeout)
                if response.status_code == 429:
                    sleepTime = int(response.headers["Retry-After"])+1
                    self.SleepAndPrintTime(sleepTime)
                else:
                    break
        except requests.exceptions.RequestException:
            raise

        if downloadFile:
            return response
        
        try:
            response.raise_for_status()
            resp = response.json()
        except Exception as e:
            raise
        
        return resp


    def api_url_params(self, url, params, api_url_has_params=False):
        '''
        Add params to the url
        '''
        if params:
            # if api_url contains already params and there is already a '?' avoid
            # adding second '?' (api_url += '&' if '?' in api_url else '?'); causes
            # issues with request parametes (usually for endpoints with required
            # arguments passed as parameters)
            url += '&' if api_url_has_params else '?'
            for key, value in params.items():
                if type(value) == bool:
                    value = str(value).lower()

                url += "{0}={1}&".format(key, value)
            url = url[:-1]
        return url


    def SleepAndPrintTime(self, sleepingTime):
        '''
        Sleep and print countdown timer
        Used for a 429 response retry-aftero
        '''
        print()
        print("Retrying in %s s"%(sleepingTime))
        for i in range(sleepingTime,0,-1):
            sys.stdout.write("{:3d} seconds remaining.\r".format(i))
            sys.stdout.flush()
            time.sleep(1)
        print()

def __main__():
    pass

if __name__=='__main__':
    __main__()
        
