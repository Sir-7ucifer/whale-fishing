"""Exchange and wallet identification helpers."""
from typing import Optional

# Known Bitcoin exchange addresses
KNOWN_EXCHANGES = {
    # Binance BTC addresses
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
