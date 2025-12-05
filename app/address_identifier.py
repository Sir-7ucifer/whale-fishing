"""Exchange and wallet identification helpers."""
from typing import Optional

# Known exchange addresses (partial list - add more as needed)
KNOWN_EXCHANGES = {
    # Ethereum addresses
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance",
    "0x21a31ee1afc51d94c2efccaa2092ad1028285549": "Binance",
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": "Binance",
    "0x56eddb7aa87536c09ccc2793473599fd21a8b17f": "Binance",
    "0x9696f59e4d72e237be84ffd425dcad154bf96976": "Binance",
    "0x4e9ce36e442e55ecd9025b9a6e0d88485d628a67": "Binance",
    "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8": "Binance",
    "0xf977814e90da44bfa03b6295a0616a897441acec": "Binance",
    "0x001866ae5b3de6caa5a51543fd9fb64f524f5478": "Binance",
    "0x85b931a32a0725be14285b66f1a22178c672d69b": "Binance",
    "0x708396f17127c42383e3b9014072679b2f60b82f": "Binance",
    "0xe0f0cfde7ee664943906f17f7f14342e76a5cec7": "Binance",
    
    "0x503828976d22510aad0201ac7ec88293211d23da": "Coinbase",
    "0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740": "Coinbase",
    "0x3cd751e6b0078be393132286c442345e5dc49699": "Coinbase",
    "0xb5d85cbf7cb3ee0d56b3bb207d5fc4b82f43f511": "Coinbase",
    "0xeb2629a2734e272bcc07bda959863f316f4bd4cf": "Coinbase",
    "0xd688aea8f7d450909ade10c47faa95707b0682d9": "Coinbase",
    "0x02466e547bfdab679fc49e96bbfc62b9747d997c": "Coinbase",
    "0x6b76f8b1e9e59913bfe758821887311ba1805cab": "Coinbase",
    "0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43": "Coinbase",
    "0x77696bb39917c91a0c3908d577d5e322095425ca": "Coinbase",
    
    "0x876eabf441b2ee5b5b0554fd502a8e0600950cfa": "Kraken",
    "0xae2d4617c862309a3d75a0ffb358c7a5009c673f": "Kraken",
    "0x43984d578803891dfa9706bdeee6078d80cfc79e": "Kraken",
    "0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0": "Kraken",
    "0xfa52274dd61e1643d2205169732f29114bc240b3": "Kraken",
    "0x53d284357ec70ce289d6d64134dfac8e511c8a3d": "Kraken",
    
    "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b": "OKX",
    "0x98ec059dc3adfbdd63429454aeb0c990fba4a128": "OKX",
    "0xa7efae728d2936e78bda97dc267687568dd593f3": "OKX",
    
    "0x1151314c646ce4e0efd76d1af4760ae66a9fe30f": "Bitfinex",
    "0x742d35cc6634c0532925a3b844bc9e7595f0beb": "Bitfinex",
    "0x876eabf441b2ee5b5b0554fd502a8e0600950cfa": "Bitfinex",
    
    "0x0d0707963952f2fba59dd06f2b425ace40b492fe": "Gate.io",
    "0x1c4b70a3968436b9a0a9cf5205c787eb81bb558c": "Gate.io",
    
    "0x2910543af39aba0cd09dbb2d50200b3e800a63d2": "Bybit",
    "0xf89d7b9c864f589bbf53a82105107622b35eaa40": "Bybit",
    
    "0x46340b20830761efd32832a74d7169b29feb9758": "Crypto.com",
    "0x6262998ced04146fa42253a5c0af90ca02dfd2a3": "Crypto.com",
    
    # Bitcoin addresses (partial list)
    "bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrpmv24sq90ecnvqqjwvw97": "Binance",
    "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo": "Binance",
    "3Cbq7aT1tY8kMxWLbitaG7yT6bPbKChq64": "Binance",
    "bc1qm34lsc65zpw79lxes69zkqmk6ee3ewf0j77s3h": "Binance",
}

def identify_address(address: str) -> Optional[str]:
    """
    Identify if an address belongs to a known exchange or entity.
    Returns the entity name or None.
    """
    if not address:
        return None
    
    address_lower = address.lower()
    
    # Check known exchanges
    for known_addr, name in KNOWN_EXCHANGES.items():
        if address_lower == known_addr.lower():
            return name
    
    return None

def determine_transaction_type(from_addr: str, to_addr: str) -> str:
    """
    Determine transaction type based on sender/receiver.
    Returns: "buy", "sell", or "transfer"
    """
    from_entity = identify_address(from_addr)
    to_entity = identify_address(to_addr)
    
    if from_entity and not to_entity:
        # From exchange to unknown wallet = Withdrawal/Buy
        return "buy"
    elif to_entity and not from_entity:
        # From unknown wallet to exchange = Deposit/Sell
        return "sell"
    elif from_entity and to_entity:
        # Between exchanges = Transfer
        return "exchange transfer"
    else:
        # Between unknown wallets = Transfer
        return "transfer"
