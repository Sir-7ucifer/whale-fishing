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
        self.posted_hashes = set()  # Track posted transaction hashes
    
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
    
    async def fetch_whale_transactions(self) -> List[Dict]:
        """
        Fetch recent large transactions from free blockchain APIs.
        Returns list of transactions sorted by USD value (highest first).
        """
        logger.info("=" * 70)
        logger.info("🔍 WHALE TRANSACTION CHECK")
        logger.info("=" * 70)
        
        # Fetch BTC price
        btc_price = await price_fetcher.get_price_usd("BTC")
        
        # Format price display
        btc_str = f"${btc_price:,.2f}" if btc_price else "N/A"
        
        logger.info(f"💰 BTC PRICE: {btc_str}")
        logger.info("-" * 70)
        
        all_transactions = []
        
        # Fetch BTC transactions
        btc_txs = await self.fetch_btc_transactions()
        
        # Log results
        logger.info("📊 NETWORK RESULTS:")
        logger.info(f"   BTC: {len(btc_txs) if isinstance(btc_txs, list) else 'ERROR'} transactions")
        
        # Add BTC transactions to results
        if isinstance(btc_txs, list):
            all_transactions.extend(btc_txs)
        
        # Sort by USD value (highest first)
        all_transactions.sort(key=lambda x: x["amount_usd"], reverse=True)
        
        if all_transactions:
            logger.info(f"✅ WHALE ALERTS: {len(all_transactions)} transaction(s) over ${config.usd_threshold:,.0f}")
        else:
            logger.info(f"⚠️  NO WHALES: No transactions over ${config.usd_threshold:,.0f}")
        logger.info("=" * 70)

        return all_transactions
    
    async def process_highest_transaction(self):
        """Fetch transactions and post all whale transactions to Discord."""
        transactions = await self.fetch_whale_transactions()
        
        if not transactions:
            return
        
        logger.info("")
        logger.info("📤 POSTING TRANSACTIONS")
        logger.info("-" * 70)
        
        # Post each transaction to Discord (skip duplicates)
        posted_count = 0
        for idx, tx in enumerate(transactions, 1):
            # Skip if already posted
            if tx['hash'] in self.posted_hashes:
                logger.debug(f"   ⏭️  Skipped (duplicate): {tx['hash'][:16]}...")
                continue
            
            logger.info(f"   [{idx}] {tx['asset']} | ${tx['amount_usd']:,.0f} | {tx['amount']:,.4f} {tx['asset']}")
            
            # Identify exchanges and determine transaction type
            from_entity = identify_address(tx['from'])
            to_entity = identify_address(tx['to'])
            tx_type = determine_transaction_type(tx['from'], tx['to'])
            
            # Build owner info if available
            from_info = tx['from']
            if from_entity:
                from_info = f"{from_entity} ({from_info})"
            elif tx['from_owner']:
                from_info = f"{tx['from_owner']} ({from_info})"
            
            to_info = tx['to']
            if to_entity:
                to_info = f"{to_entity} ({to_info})"
            elif tx['to_owner']:
                to_info = f"{tx['to_owner']} ({to_info})"
            
            # Post to Discord
            success = await discord_poster.post_whale_alert(
                asset=tx['asset'],
                amount=tx['amount'],
                usd_value=tx['amount_usd'],
                sender=from_info,
                receiver=to_info,
                tx_hash=tx['hash'],
                transaction_type=tx_type
            )
            
            if success:
                # Track this transaction to avoid duplicates
                self.posted_hashes.add(tx['hash'])
                posted_count += 1
                logger.info("        ✅ Posted to Discord")
                # Small delay between posts to avoid rate limiting
                await asyncio.sleep(1)
            else:
                logger.error(f"        ❌ Failed to post {tx['asset']} transaction")
        
        if posted_count > 0:
            logger.info("-" * 70)
            logger.info(f"🎉 SUCCESS: Posted {posted_count} new transaction(s) to Discord")
            logger.info("=" * 70)
        else:
            logger.info("-" * 70)
            logger.info("⏭️  All transactions already posted")
            logger.info("=" * 70)
    
    async def monitor_loop(self):
        """Main monitoring loop that checks every second for real-time updates."""
        logger.info("")
        logger.info("▶️  Monitoring loop started")
        logger.info(f"⏱️  Check interval: {self.check_interval} second(s)")
        logger.info("")
        self.is_running = True
        
        check_count = 0
        while self.is_running:
            try:
                check_count += 1
                await self.process_highest_transaction()
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            # Wait before next check (1 second for fast updates)
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
