"""Blockchain monitoring service that polls for whale transactions."""
import asyncio
import logging
from typing import List, Dict
import httpx

from app.config import config
from app.pricing import price_fetcher
from app.discord_poster import discord_poster
from app.address_identifier import identify_address, determine_transaction_type

logger = logging.getLogger(__name__)


class BlockchainMonitor:
    """Monitors blockchain APIs for large transactions."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.is_running = False
        self.check_interval = config.check_interval
        
    async def fetch_eth_transactions(self) -> List[Dict]:
        """Fetch recent large ETH transactions from Etherscan."""
        try:
            url = "https://api.etherscan.io/api"
            params = {
                "module": "account",
                "action": "txlist",
                "address": "0xdac17f958d2ee523a2206206994597c13d831ec7",  # USDT contract as proxy for activity
                "startblock": 0,
                "endblock": 99999999,
                "page": 1,
                "offset": 50,
                "sort": "desc"
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            transactions = []
            if data.get("status") == "1" and data.get("result"):
                for tx in data["result"][:20]:  # Check last 20 transactions
                    amount_wei = float(tx.get("value", 0))
                    amount_eth = amount_wei / 1e18
                    
                    if amount_eth > 0:  # Only process transactions with value
                        price = await price_fetcher.get_price_usd("ETH")
                        if price:
                            usd_value = amount_eth * price
                            if usd_value >= config.usd_threshold:
                                transactions.append({
                                    "asset": "ETH",
                                    "amount": amount_eth,
                                    "amount_usd": usd_value,
                                    "from": tx.get("from", "Unknown"),
                                    "from_owner": None,
                                    "to": tx.get("to", "Unknown"),
                                    "to_owner": None,
                                    "hash": tx.get("hash", ""),
                                    "timestamp": int(tx.get("timeStamp", 0))
                                })
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error fetching ETH transactions: {e}")
            return []
    
    async def fetch_btc_transactions(self) -> List[Dict]:
        """Fetch recent large BTC transactions from Blockchain.com API."""
        try:
            # Get latest blocks
            url = "https://blockchain.info/latestblock"
            response = await self.client.get(url)
            response.raise_for_status()
            latest = response.json()
            block_height = latest.get("height", 0)
            
            # Get recent block
            block_url = f"https://blockchain.info/block-height/{block_height}?format=json"
            response = await self.client.get(block_url)
            response.raise_for_status()
            block_data = response.json()
            
            transactions = []
            if "blocks" in block_data:
                for block in block_data["blocks"][:1]:  # Just check latest block
                    for tx in block.get("tx", [])[:10]:  # Check up to 10 txs
                        total_output = sum([out.get("value", 0) for out in tx.get("out", [])])
                        amount_btc = total_output / 1e8
                        
                        if amount_btc > 0:
                            price = await price_fetcher.get_price_usd("BTC")
                            if price:
                                usd_value = amount_btc * price
                                if usd_value >= config.usd_threshold:
                                    from_addr = tx.get("inputs", [{}])[0].get("prev_out", {}).get("addr", "Unknown")
                                    to_addr = tx.get("out", [{}])[0].get("addr", "Unknown")
                                    
                                    transactions.append({
                                        "asset": "BTC",
                                        "amount": amount_btc,
                                        "amount_usd": usd_value,
                                        "from": from_addr,
                                        "from_owner": None,
                                        "to": to_addr,
                                        "to_owner": None,
                                        "hash": tx.get("hash", ""),
                                        "timestamp": tx.get("time", 0)
                                    })
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error fetching BTC transactions: {e}")
            return []
    
    async def fetch_xrp_transactions(self) -> List[Dict]:
        """Fetch recent large XRP transactions from XRP Scan API."""
        try:
            response = await self.client.get("https://xrpscan.com/api/v2/transactions/recent")
            response.raise_for_status()
            data = response.json()
            
            transactions = []
            if "transactions" in data:
                for tx in data["transactions"][:30]:  # Check last 30 transactions
                    # Look for Payment transactions with value
                    if tx.get("type") == "Payment":
                        amount_drops = float(tx.get("amount", 0))
                        if isinstance(amount_drops, dict):
                            continue  # Skip token payments, only native XRP
                        
                        amount_xrp = amount_drops / 1e6  # Convert drops to XRP
                        
                        if amount_xrp > 0:
                            price = await price_fetcher.get_price_usd("XRP")
                            if price:
                                usd_value = amount_xrp * price
                                if usd_value >= config.usd_threshold:
                                    transactions.append({
                                        "asset": "XRP",
                                        "amount": amount_xrp,
                                        "amount_usd": usd_value,
                                        "from": tx.get("account", "Unknown"),
                                        "from_owner": None,
                                        "to": tx.get("destination", "Unknown"),
                                        "to_owner": None,
                                        "hash": tx.get("hash", ""),
                                        "timestamp": int(tx.get("closeTime", 0))
                                    })
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error fetching XRP transactions: {e}")
            return []
    
    async def fetch_sol_transactions(self) -> List[Dict]:
        """Fetch recent large SOL transactions from Solscan API."""
        try:
            # Using Solscan API for transaction data
            response = await self.client.get("https://api.solscan.io/api/v2/transfer")
            response.raise_for_status()
            data = response.json()
            
            transactions = []
            if "data" in data:
                for tx in data["data"][:30]:  # Check last 30 transactions
                    amount_lamports = float(tx.get("amount", 0))
                    amount_sol = amount_lamports / 1e9  # Convert lamports to SOL
                    
                    if amount_sol > 0:
                        price = await price_fetcher.get_price_usd("SOL")
                        if price:
                            usd_value = amount_sol * price
                            if usd_value >= config.usd_threshold:
                                transactions.append({
                                    "asset": "SOL",
                                    "amount": amount_sol,
                                    "amount_usd": usd_value,
                                    "from": tx.get("from", "Unknown"),
                                    "from_owner": None,
                                    "to": tx.get("to", "Unknown"),
                                    "to_owner": None,
                                    "hash": tx.get("signature", ""),
                                    "timestamp": int(tx.get("blockTime", 0))
                                })
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error fetching SOL transactions: {e}")
            return []
    
    async def fetch_whale_transactions(self) -> List[Dict]:
        """
        Fetch recent large transactions from free blockchain APIs.
        Returns list of transactions sorted by USD value (highest first).
        """
        logger.info("Fetching whale transactions from blockchain explorers...")
        
        all_transactions = []
        
        # Fetch from different chains in parallel
        eth_task = self.fetch_eth_transactions()
        btc_task = self.fetch_btc_transactions()
        xrp_task = self.fetch_xrp_transactions()
        sol_task = self.fetch_sol_transactions()
        
        eth_txs, btc_txs, xrp_txs, sol_txs = await asyncio.gather(
            eth_task, btc_task, xrp_task, sol_task, return_exceptions=True
        )
        
        # Combine results (handle exceptions)
        if isinstance(eth_txs, list):
            all_transactions.extend(eth_txs)
        if isinstance(btc_txs, list):
            all_transactions.extend(btc_txs)
        if isinstance(xrp_txs, list):
            all_transactions.extend(xrp_txs)
        if isinstance(sol_txs, list):
            all_transactions.extend(sol_txs)
        
        # Sort by USD value (highest first)
        all_transactions.sort(key=lambda x: x["amount_usd"], reverse=True)
        
        logger.info(f"Found {len(all_transactions)} whale transactions above ${config.usd_threshold:,.0f}")
        return all_transactions
    
    async def process_highest_transaction(self):
        """Fetch transactions and post the highest valued one to Discord."""
        transactions = await self.fetch_whale_transactions()
        
        if not transactions:
            logger.info("No whale transactions found in the last 10 minutes")
            return
        
        # Get the highest valued transaction
        highest = transactions[0]
        
        logger.info(
            f"Highest transaction: {highest['asset']} "
            f"${highest['amount_usd']:,.0f} "
            f"({highest['amount']:,.4f} {highest['asset']})"
        )
        
        # Identify exchanges and determine transaction type
        from_entity = identify_address(highest['from'])
        to_entity = identify_address(highest['to'])
        tx_type = determine_transaction_type(highest['from'], highest['to'])
        
        # Build owner info if available
        from_info = highest['from']
        if from_entity:
            from_info = f"{from_entity} ({from_info})"
        elif highest['from_owner']:
            from_info = f"{highest['from_owner']} ({from_info})"
        
        to_info = highest['to']
        if to_entity:
            to_info = f"{to_entity} ({to_info})"
        elif highest['to_owner']:
            to_info = f"{highest['to_owner']} ({to_info})"
        
        # Post to Discord
        success = await discord_poster.post_whale_alert(
            asset=highest['asset'],
            amount=highest['amount'],
            usd_value=highest['amount_usd'],
            sender=from_info,
            receiver=to_info,
            tx_hash=highest['hash'],
            transaction_type=tx_type
        )
        
        if success:
            logger.info("Successfully posted highest transaction to Discord")
        else:
            logger.error("Failed to post highest transaction to Discord")
    
    async def monitor_loop(self):
        """Main monitoring loop that checks every 10 minutes."""
        logger.info(f"Starting blockchain monitoring (checking every {self.check_interval}s)")
        self.is_running = True
        
        while self.is_running:
            try:
                await self.process_highest_transaction()
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            # Wait 10 minutes before next check
            logger.info(f"Waiting {self.check_interval} seconds until next check...")
            await asyncio.sleep(self.check_interval)
    
    async def start(self):
        """Start the monitoring loop as a background task."""
        if not self.is_running:
            asyncio.create_task(self.monitor_loop())
    
    async def stop(self):
        """Stop the monitoring loop."""
        logger.info("Stopping blockchain monitor...")
        self.is_running = False
        await self.client.aclose()


# Global monitor instance
blockchain_monitor = BlockchainMonitor()
