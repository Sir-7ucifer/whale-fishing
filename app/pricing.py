"""Price fetching and caching for crypto assets."""
import time
import logging
from typing import Dict, Optional
import httpx

from app.config import config

logger = logging.getLogger(__name__)


class PriceCache:
    """Simple in-memory price cache with TTL."""
    
    def __init__(self, ttl_seconds: int = 60):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, tuple[float, float]] = {}  # symbol -> (price, timestamp)
    
    def get(self, symbol: str) -> Optional[float]:
        """Get cached price if still valid."""
        if symbol not in self._cache:
            return None
        
        price, timestamp = self._cache[symbol]
        if time.time() - timestamp > self.ttl_seconds:
            del self._cache[symbol]
            return None
        
        return price
    
    def set(self, symbol: str, price: float):
        """Cache a price with current timestamp."""
        self._cache[symbol] = (price, time.time())


class PriceFetcher:
    """Fetches current USD prices for crypto assets."""
    
    def __init__(self):
        self.cache = PriceCache(ttl_seconds=config.price_cache_ttl_seconds)
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def get_price_usd(self, asset: str) -> Optional[float]:
        """
        Get current USD price for an asset.
        First checks cache, then fetches from CoinGecko if needed.
        """
        # Check cache first
        cached_price = self.cache.get(asset)
        if cached_price is not None:
            logger.debug(f"Using cached price for {asset}: ${cached_price:,.2f}")
            return cached_price
        
        # Fetch from CoinGecko
        if asset not in config.assets:
            logger.warning(f"Asset {asset} not configured")
            return None
        
        coingecko_id = config.assets[asset].coingecko_id
        
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": coingecko_id,
                "vs_currencies": "usd"
            }
            
            # Add API key if configured
            headers = {}
            if config.coingecko_api_key:
                headers["x-cg-pro-api-key"] = config.coingecko_api_key
            
            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if coingecko_id in data and "usd" in data[coingecko_id]:
                price = float(data[coingecko_id]["usd"])
                self.cache.set(asset, price)
                logger.info(f"Fetched price for {asset}: ${price:,.2f}")
                return price
            
            logger.error(f"Price not found in CoinGecko response for {asset}")
            return None
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching price for {asset}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching price for {asset}: {e}")
            return None
    
    async def get_all_prices(self) -> Dict[str, Optional[float]]:
        """
        Fetch all configured asset prices in a single API call.
        More efficient and avoids rate limiting.
        """
        # Check cache for all assets
        prices = {}
        assets_to_fetch = []
        
        for asset in ["BTC"]:
            cached = self.cache.get(asset)
            if cached is not None:
                prices[asset] = cached
            else:
                assets_to_fetch.append(asset)
        
        # If all cached, return early
        if not assets_to_fetch:
            return prices
        
        # Batch fetch from CoinGecko
        try:
            coingecko_ids = [config.assets[a].coingecko_id for a in assets_to_fetch]
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": ",".join(coingecko_ids),
                "vs_currencies": "usd"
            }
            
            headers = {}
            if config.coingecko_api_key:
                headers["x-cg-pro-api-key"] = config.coingecko_api_key
            
            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Map back to asset symbols and cache
            for asset in assets_to_fetch:
                coingecko_id = config.assets[asset].coingecko_id
                if coingecko_id in data and "usd" in data[coingecko_id]:
                    price = float(data[coingecko_id]["usd"])
                    self.cache.set(asset, price)
                    prices[asset] = price
                    logger.info(f"Fetched price for {asset}: ${price:,.2f}")
                else:
                    prices[asset] = None
                    logger.warning(f"Price not found for {asset}")
            
            return prices
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching batch prices: {e}")
            # Return None for unfetched assets
            for asset in assets_to_fetch:
                prices[asset] = None
            return prices
        except Exception as e:
            logger.error(f"Unexpected error fetching batch prices: {e}")
            for asset in assets_to_fetch:
                prices[asset] = None
            return prices
    
    async def calculate_usd_value(self, asset: str, amount: float) -> Optional[float]:
        """Calculate USD value for a given amount of an asset."""
        price = await self.get_price_usd(asset)
        if price is None:
            return None
        return amount * price
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global price fetcher instance
price_fetcher = PriceFetcher()
