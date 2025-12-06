"""Configuration management for Whale Tracker bot."""
import os
from typing import Dict, List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class AssetConfig(BaseModel):
    """Configuration for a single asset."""
    symbol: str
    coingecko_id: str
    explorer_url: str


class Config(BaseModel):
    """Application configuration."""
    discord_webhook_url: str = Field(default_factory=lambda: os.getenv("DISCORD_WEBHOOK_URL", ""))
    usd_threshold: float = Field(default_factory=lambda: float(os.getenv("USD_THRESHOLD", "1000000")))
    coingecko_api_key: str = Field(default_factory=lambda: os.getenv("COINGECKO_API_KEY", ""))
    check_interval: int = Field(default_factory=lambda: int(os.getenv("CHECK_INTERVAL", "1")))
    price_cache_ttl_seconds: int = Field(default_factory=lambda: int(os.getenv("PRICE_CACHE_TTL", "60")))
    
    # Supported assets with explorer URLs
    assets: Dict[str, AssetConfig] = {
        "BTC": AssetConfig(
            symbol="BTC",
            coingecko_id="bitcoin",
            explorer_url="https://blockchain.com/btc/tx/{tx_hash}"
        ),
        "ETH": AssetConfig(
            symbol="ETH",
            coingecko_id="ethereum",
            explorer_url="https://etherscan.io/tx/{tx_hash}"
        ),
        "XRP": AssetConfig(
            symbol="XRP",
            coingecko_id="ripple",
            explorer_url="https://xrpscan.com/tx/{tx_hash}"
        ),
        "SOL": AssetConfig(
            symbol="SOL",
            coingecko_id="solana",
            explorer_url="https://solscan.io/tx/{tx_hash}"
        ),
    }
    
    @property
    def supported_assets(self) -> List[str]:
        """Return list of supported asset symbols."""
        return list(self.assets.keys())
    
    def get_explorer_url(self, asset: str, tx_hash: str) -> str:
        """Generate explorer URL for a transaction."""
        if asset not in self.assets:
            return ""
        return self.assets[asset].explorer_url.format(tx_hash=tx_hash)
    
    def validate_config(self) -> List[str]:
        """Validate required configuration and return list of errors."""
        errors = []
        if not self.discord_webhook_url:
            errors.append("DISCORD_WEBHOOK_URL is required")
        if self.usd_threshold <= 0:
            errors.append("USD_THRESHOLD must be positive")
        return errors


# Global config instance
config = Config()
