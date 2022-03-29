'''
Created on Feb 25, 2022

@author: arno

Lookup the meaning of the methodid from a transactions

1: getMethod4ByteDir(txMethodId)
First way is through the dictionary site 4bytes
There is possibility that multiple functions are returned

2: getMethodContract(methodId, contractAddr)
second way is through retrieving contract from etherscan and calculating 
each hash of the functions, when there is a function implementation then the search
goes further with the provided proxy contract address. (this only works when 
this implementation function is public)

The methodid is the sha256 hash from the string FunctionName(inputtype1,inputtype2,...)
The methodid is the first 8 characters of the hash with 0x in front (total of 10 chars)

'''
from web3 import Web3
import requests
import config
from datetime import datetime, timezone
import json
from sha3 import keccak_256


ethAddress = Web3.toChecksumAddress(config.ETH_ADDRESS[3])
#ethAddress = '0x2c1ba59d6f58433fb1eaee7d20b26ed83bda51a3' #internal tx
#ethAddress = '0x4e83362442b8d1bec281594cea3050c8eb01311c' # token
#ethAddress = '0x6975be450864c02b4613023c2152ee0743572325' # NFT
#ethAddress = '0x9dd134d14d1e65f84b706d6f205cd5b1cd03a46b' # mined block



def getMethod4ByteDir(methodId):
    if len(methodId) != 10:
        return ''
    
    urlGetMethod = 'https://www.4byte.directory/api/v1/signatures/?hex_signature=' + methodId
    responseMethod = requests.request("GET", urlGetMethod)
    respMethod = responseMethod.json()
    #print(respMethod)
    methodFunction = ''
    for j in respMethod['results']:
        methodFunction += j['text_signature'] + ';'
    return methodFunction


def getContractImplementation(contractAddr):
    web3 = Web3(Web3.HTTPProvider(config.ETH_HTTP_PROVIDER2))
    if (not web3.isConnected()):
        print("No ethereum provider, Web3 disconnected")
        return ''
    contract = web3.eth.contract(address=Web3.toChecksumAddress(contractAddr.lower()), abi=config.IMPLEMENT_ABI)
    implementation_address = contract.functions.implementation().call() 
    print('Using Proxy contract: %s'%(implementation_address))
    return implementation_address


def getMethodContract(methodId, contractAddr):
    if len(methodId) != 10 or contractAddr == '':
        return ''
    
    urlGetContractABI = config.ETHERSCAN_URL + \
                '?module=contract&action=getabi&address=' + \
                contractAddr + '&apikey=' + \
                config.ETHERSCAN_API
    responseMethod = requests.request("GET", urlGetContractABI)
    respMethod = responseMethod.json()
    respMethodResult = respMethod['result']
    res = json.loads(respMethodResult)
    print('-start Contract: %s'%(contractAddr))
    for i in res:
        #for k,v in i.items():
        #    print('%s: %s'%(k,v))
        if "inputs" in i and "name" in i:
            contrName = i['name']
            #contrInputs = i['inputs']
            contrInputTypes = []
            for inp in i['inputs']:
                contrInputTypes.append(inp['type'])
            contrInputTypeStr = ','.join(contrInputTypes)
            #print('%s( %s )'%(contrName, contrInputs))
            #print('%s(%s)'%(contrName, contrInputTypeStr))
            contrMethod = '%s(%s)'%(contrName, contrInputTypeStr)
            sha3_hash = keccak_256(contrMethod.encode('utf-8')).hexdigest()
            contrMethodId = '0x'+sha3_hash[:8]
            #print('%s %s'%(contrMethodId, contrMethod))
            if contrMethodId == methodId:
                return contrMethod
            
            # check for proxy contract implementation
            if contrName == 'implementation':
                contrProxy = getContractImplementation(contractAddr)
                if contrProxy != '':
                    return getMethodContract(methodId, contrProxy)
        #print()
    #print('----')
    # not method found
    return 'No method found'


def __main__():
    print('Get a list of "Normal" Transactions By Address')
    urlEthTxlist =  config.ETHERSCAN_URL + \
                    '?module=account&action=txlist&address=' + \
                    ethAddress + '&startblock=0&endblock=latest&sort=asc&apikey=' + \
                    config.ETHERSCAN_API
    response = requests.request("GET", urlEthTxlist)
    resp = response.json()
    print('number of tx: ', len(resp['result']))
    #print(resp)
    for i in resp['result']:
        txBlock = i['blockNumber']
        txTime = datetime.fromtimestamp(int(i['timeStamp']), tz=timezone.utc)
        txHash = i['hash']
        txNonce = i['nonce']
        txBlockHash = i['blockHash']
        txTransactionIndex = i['transactionIndex']
        txFrom = i['from']
        txTo = i['to']
        txValue = int(i['value']) / 10**18
        txGas = int(i['gas'])
        txGasPrice = int(i['gasPrice'])
        txGasUsed = int(i['gasUsed'])
        txIsError = i['isError']
        txReceipt_status = i['txreceipt_status']
        txInput = i['input']
        txContractAddress = i['contractAddress']
        txGasUsed = int(i['gasUsed'])
        txCumulativeGasUsed = int(i['cumulativeGasUsed'])
        txConfirmations = int(i['confirmations'])
        txFee = txGasPrice * txGasUsed / 10**18
        txMethodId = txInput[:10]
        txMethod1 = getMethod4ByteDir(txMethodId)
        if ethAddress.lower() == txFrom.lower():
            contractAddr = txTo
        elif ethAddress.lower() == txTo.lower():
            contractAddr = txFrom
        else:
            contractAddr = txContractAddress
        txMethod2 = getMethodContract(txMethodId, contractAddr)
    
        print("From: %s -> To: %s, Contract: %s\n method: %s\n%s\n%s"%
              (txFrom, txTo, txContractAddress, txMethodId, txMethod1, txMethod2))
    print()

if __name__=='__main__':
    __main__()