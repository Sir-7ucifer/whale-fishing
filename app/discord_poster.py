"""Discord webhook posting with retry logic."""
import logging
from typing import Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import config

logger = logging.getLogger(__name__)


class DiscordPoster:
    """Posts whale alerts to Discord via webhook."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True
    )
    async def _post_with_retry(self, webhook_url: str, payload: dict) -> httpx.Response:
        """Post to Discord with automatic retry on transient failures."""
        response = await self.client.post(webhook_url, json=payload)
        response.raise_for_status()
        return response
    
    async def post_whale_alert(
        self,
        asset: str,
        amount: float,
        usd_value: float,
        sender: str,
        receiver: str,
        tx_hash: str,
        transaction_type: Optional[str] = None,
    ) -> bool:
        """
        Post a whale transaction alert to Discord.
        
        Returns True if successfully posted, False otherwise.
        """
        if not config.discord_webhook_url:
            logger.error("Discord webhook URL not configured")
            return False
        
        # Build explorer link
        explorer_url = config.get_explorer_url(asset, tx_hash)
        
        # Determine transaction type emoji and color
        type_emoji = "🔄"
        color = 0xFF6B35  # Orange (default)
        type_text = "Transfer"
        
        if transaction_type:
            if "exchange" in transaction_type.lower() or "buy" in transaction_type.lower():
                type_emoji = "📈"
                color = 0x00FF00  # Green
                type_text = "Buy/Exchange Deposit"
            elif "sell" in transaction_type.lower() or "withdraw" in transaction_type.lower():
                type_emoji = "📉"
                color = 0xFF0000  # Red
                type_text = "Sell/Exchange Withdrawal"
        
        # Format the message
        embed = {
            "title": f"{type_emoji} Whale Alert: {type_text}",
            "color": color,
            "fields": [
                {
                    "name": "Asset",
                    "value": asset,
                    "inline": True
                },
                {
                    "name": "Amount",
                    "value": f"{amount:,.4f} {asset}",
                    "inline": True
                },
                {
                    "name": "USD Value",
                    "value": f"${usd_value:,.0f}",
                    "inline": True
                },
                {
                    "name": "Type",
                    "value": type_text,
                    "inline": True
                },
                {
                    "name": "From",
                    "value": f"`{sender[:16]}...{sender[-8:]}`" if len(sender) > 24 else f"`{sender}`",
                    "inline": False
                },
                {
                    "name": "To",
                    "value": f"`{receiver[:16]}...{receiver[-8:]}`" if len(receiver) > 24 else f"`{receiver}`",
                    "inline": False
                },
                {
                    "name": "Transaction",
                    "value": f"[View on Explorer]({explorer_url})" if explorer_url else f"`{tx_hash}`",
                    "inline": False
                }
            ],
            "footer": {
                "text": "Whale Tracker Bot"
            }
        }
        
        payload = {
            "embeds": [embed]
        }
        
        try:
            await self._post_with_retry(config.discord_webhook_url, payload)
            logger.info(
                f"Posted whale alert to Discord: {asset} ${usd_value:,.0f} "
                f"(tx: {tx_hash[:16]}...)"
            )
            return True
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to post to Discord after retries: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error posting to Discord: {e}")
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global Discord poster instance
discord_poster = DiscordPoster()
