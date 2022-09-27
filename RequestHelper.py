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
        '''
        Initialization of the session 
        '''
        session = requests.Session()
        #session.headers.update({'Accept': 'application/json'})
        retry = Retry(total=5, backoff_factor=1.5, 
                      respect_retry_after_header=True, 
                      status_forcelist=[502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session


    def updateHeader(self, params:dict):
        '''
        Update the header of the session 

        params = dictionary with parameters for the header
        '''
        self.session.headers.update(params)
        

    def getRequestResponse(self, url, downloadFile = False, stream=False):
        '''
        general request url function 
        should be a class, with _init etc

        url = api url for request
        downloadFile = request is for downloading a file
                       (no convertion to json)
        '''

        # debug info
        #print('Inside RequestHelper.getRequestResponse')
        #print('URL: ', url)

        resp = []
        request_timeout = 120

        try:
            while True:
                response = self.session.get(url, timeout=request_timeout, stream=stream, verify=True)
                if response.status_code == 429:
                    if "Retry-After" in response.headers.keys():
                        sleepTime = int(response.headers["Retry-After"])+1
                        self.SleepAndPrintTime(sleepTime)
                    else:
                        raise requests.exceptions.RequestException
                else:
                    break
        except requests.exceptions.RequestException:
            print("Header request exception:", response.headers)
            print(response.text)
            raise
        except Exception:
            print("Header exception:", response.headers)
            print(response.text)
            raise

        if downloadFile:
            return response
        
        try:
            resp = response.json()
        except Exception as e:
            print('JSON Exception: ', e)

        try:
            response.raise_for_status()
            if isinstance(resp, list):
                resp = {'result': resp}

            resp['status_code'] = response.status_code
        except requests.exceptions.HTTPError as e:
            print('No status Exception: ', e)
        except Exception as e:
            print('Other Exception: ', e)#, response.json())
            #raise
            resp['status_code'] = "error" # response.text
            resp['prices'] = ""
        
        return resp


    def api_url_params(self, url, params:dict, api_url_has_params=False):
        '''
        Add params to the url

        url = url to be extended with parameters
        params = dictionary of parameters
        api_url_has_params = bool to extend url with '?' or '&'
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
        Used for a 429 response retry-after

        sleepingTime = total time to sleep in seconds
        '''
        print()
        print("Retrying in %s s"%(sleepingTime))
        for i in range(sleepingTime,0,-1):
            print("\r{:3d} seconds remaining.".format(i), end="", flush=True)
            time.sleep(1)
        print()

def __main__():
    pass

if __name__=='__main__':
    __main__()
        
