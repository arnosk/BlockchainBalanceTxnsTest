"""
Created on Feb 25, 2022

@author: arno

Lookup the meaning of the method_id from a transactions

1: get_method4byte_dir(txMethod_id)
First way is through the dictionary site 4bytes
There is possibility that multiple functions are returned

2: get_method_contract(method_id, contract_addr)
second way is through retrieving contract from etherscan and calculating 
each hash of the functions, when there is a function implementation then the search
goes further with the provided proxy contract address. (this only works when 
this implementation function is public)

The method_id is the sha256 hash from the string FunctionName(inputtype1,inputtype2,...)
The method_id is the first 8 characters of the hash with 0x in front (total of 10 chars)

"""
from web3 import Web3
import requests
import config
from datetime import datetime, timezone
import json
from sha3 import keccak_256


eth_address = Web3.toChecksumAddress(config.ETH_ADDRESS[3])
#eth_address = '0x2c1ba59d6f58433fb1eaee7d20b26ed83bda51a3' #internal tx
#eth_address = '0x4e83362442b8d1bec281594cea3050c8eb01311c' # token
#eth_address = '0x6975be450864c02b4613023c2152ee0743572325' # NFT
#eth_address = '0x9dd134d14d1e65f84b706d6f205cd5b1cd03a46b' # mined block



def get_method4byte_dir(method_id):
    """Search for ethereum signature method on www.4byte.directory
    
    Function calls in the Ethereum Virtual Machine are specified by the first
    four bytes of data sent with a transaction. These 4-byte signatures are 
    defined as the first four bytes of the Keccak hash (SHA3) of the canonical 
    representation of the function signature
    """
    if len(method_id) != 10:
        return ''
    
    url_getmethod = 'https://www.4byte.directory/api/v1/signatures/?hex_signature=' + method_id
    response_method = requests.request('GET', url_getmethod)
    resp_method = response_method.json()
    #print(resp_method)
    method_function = ''
    for j in resp_method['results']:
        method_function += j['text_signature'] + ';'
    return method_function


def get_contract_implementation(contract_addr):
    """When a contract is a proxy contract, this function gets the implementation contract address
    
    This is only possible when proxy contract are public
    """
    web3 = Web3(Web3.HTTPProvider(config.ETH_HTTP_PROVIDER2))
    if (not web3.isConnected()):
        print('No ethereum provider, Web3 disconnected')
        return ''
    contract = web3.eth.contract(address=Web3.toChecksumAddress(contract_addr.lower()), abi=config.IMPLEMENT_ABI)
    implementation_address = contract.functions.implementation().call() 
    print('Using Proxy contract: %s'%(implementation_address))
    return implementation_address


def get_method_contract(method_id, contract_addr):
    """Retrieve the contract method function name from etherscan
    
    Reads all functions of a contract,
    When method_id correspond with method_id from one of these functions, return a readable function name
    When there is a implementation function, also search the implementation contract address for methods
    """
    if len(method_id) != 10 or contract_addr == '':
        return ''
    
    url_getcontractABI = config.ETHERSCAN_URL + \
                '?module=contract&action=getabi&address=' + \
                contract_addr + '&apikey=' + \
                config.ETHERSCAN_API
    response_method = requests.request('GET', url_getcontractABI)
    resp_method = response_method.json()
    resp_method_result = resp_method['result']
    res = json.loads(resp_method_result)
    print('-start Contract: %s'%(contract_addr))
    for i in res:
        #for k,v in i.items():
        #    print('%s: %s'%(k,v))
        if 'inputs' in i and 'name' in i:
            contr_name = i['name']
            #contr_inputs = i['inputs']
            contr_input_types = []
            for inp in i['inputs']:
                contr_input_types.append(inp['type'])
            contr_input_type_str = ','.join(contr_input_types)
            #print('%s( %s )'%(contr_name, contr_inputs))
            #print('%s(%s)'%(contr_name, contr_input_type_str))
            contr_method = '%s(%s)'%(contr_name, contr_input_type_str)
            sha3_hash = keccak_256(contr_method.encode('utf-8')).hexdigest()
            contr_method_id = '0x'+sha3_hash[:8]
            #print('%s %s'%(contr_method_id, contr_method))
            if contr_method_id == method_id:
                return contr_method
            
            # check for proxy contract implementation
            if contr_name == 'implementation':
                contr_proxy = get_contract_implementation(contract_addr)
                if contr_proxy != '':
                    return get_method_contract(method_id, contr_proxy)
        #print()
    #print('----')
    # no method found
    return 'No method found'


def __main__():
    """Get a list of normal transactions for an address
    """
    print('Get a list of "Normal" Transactions By Address')
    url_ethtxlist =  config.ETHERSCAN_URL + \
                    '?module=account&action=txlist&address=' + \
                    eth_address + '&startblock=0&endblock=latest&sort=asc&apikey=' + \
                    config.ETHERSCAN_API
    response = requests.request('GET', url_ethtxlist)
    resp = response.json()
    print('number of tx: ', len(resp['result']))
    #print(resp)
    for i in resp['result']:
        tx_block = i['blockNumber']
        tx_time = datetime.fromtimestamp(int(i['timeStamp']), tz=timezone.utc)
        tx_hash = i['hash']
        tx_nonce = i['nonce']
        tx_blockhash = i['blockHash']
        tx_transactionindex = i['transactionIndex']
        tx_from = i['from']
        tx_to = i['to']
        tx_value = int(i['value']) / 10**18
        tx_gas = int(i['gas'])
        tx_gas_price = int(i['gasPrice'])
        tx_gas_used = int(i['gasUsed'])
        tx_is_error = i['isError']
        tx_receipt_status = i['txreceipt_status']
        tx_input = i['input']
        tx_contract_address = i['contract_address']
        tx_gasused = int(i['gasUsed'])
        tx_cumulative_gas_used = int(i['cumulativeGasUsed'])
        txConfirmations = int(i['confirmations'])
        tx_fee = tx_gas_price * tx_gas_used / 10**18
        tx_method_id = tx_input[:10]
        tx_method1 = get_method4byte_dir(tx_method_id)
        if eth_address.lower() == tx_from.lower():
            contract_addr = tx_to
        elif eth_address.lower() == tx_to.lower():
            contract_addr = tx_from
        else:
            contract_addr = tx_contract_address
        tx_method2 = get_method_contract(tx_method_id, contract_addr)
    
        print('From: %s -> To: %s, Contract: %s\n method: %s\n%s\n%s'%
              (tx_from, tx_to, tx_contract_address, tx_method_id, tx_method1, tx_method2))
    print()

if __name__=='__main__':
    __main__()