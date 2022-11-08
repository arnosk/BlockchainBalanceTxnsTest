# Database setup
# setup for postgresql
#DB_TYPE = 'postgresql'
#DB_CONFIG = {'host':'localhost','port':'5432','dbname':'Arkofolio','user':'postgresql','password':'postgresql','mode':None}
# setup for sqlite3
DB_TYPE = 'sqlite'
DB_CONFIG = {'dbname':'Arkofolio.db'}

# Output path (relative or absolute)
# Use / or \\ for folders
OUTPUT_PATH = 'output'

# ethereum addresses
ETH_ADDRESS = ['0x2c1ba59d6f58433fb1eaee7d20b26ed83bda51a3', # internal tx
               '0x4e83362442b8d1bec281594cea3050c8eb01311c', # token
               '0x6975be450864c02b4613023c2152ee0743572325', # NFT
               '0x9dd134d14d1e65f84b706d6f205cd5b1cd03a46b'] # mined block


# look at ethereumnodes.com
ETH_HTTP_PROVIDER = 'https://mainnet.eth.cloud.ava.do/'
ETH_HTTP_PROVIDER2 = 'https://api.mycryptoapi.com/eth'
BSC_HTTP_PROVIDER = 'https://bsc-dataseed1.binance.org:443'

ETHERSCAN_API = '' # Your Etherscan API
ETHERSCAN_URL = 'https://api.etherscan.io/api'

MORALIS_API_DEF = '' # Your Moralis API
MORALIS_NODE_KEY = '' # Your Moralis Node Key
MORALIS_HTTP_PROVIDER = 'https://speedy-nodes-nyc.moralis.io/'

COINGECKO_URL = 'https://api.coingecko.com/api/v3'

CRYPTOWATCH_API = '' # Your Cryptowat.ch API
CRYPTOWATCH_URL = 'https://api.cryptowat.ch'

ALCOR_URL = 'https://?.alcor.exchange/api'
ALCOR_CHAINS = ["eos","telos","wax","proton"]

WAVESEXCHANGE_API = '' # YOUR_PUBLIC_KEY
WAVESEXCHANGE_SECRET = '' # YOUR_PRIVATE_KEY

# minimal ABI
ERC20_ABI = [
    # name
    {
        'constant': True,
        'inputs': [],
        'name': 'name',
        'outputs': [{ 'name': '', 'type': 'string'}],
        'type': 'function',
    },
    # balanceOf
    {
        'constant': True,
        'inputs': [{ 'name': '_owner', 'type': 'address'}],
        'name': 'balanceOf',
        'outputs': [{ 'name': 'balance', 'type': 'uint256'}],
        'type': 'function',
    },
    # decimals
    {
        'constant': True,
        'inputs': [],
        'name': 'decimals',
        'outputs': [{ 'name': '', 'type': 'uint8'}],
        'type': 'function',
    },
    # symbol
    {
        'constant': True,
        'inputs': [],
        'name': 'symbol',
        'outputs': [{ 'name': '', 'type': 'string'}],
        'type': 'function',
    },
]

IMPLEMENT_ABI = [
    # implementation
    {
        'inputs': [],
        'name': 'implementation',
        'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}],
        'stateMutability': 'view',
        'type': 'function',
    },
]
