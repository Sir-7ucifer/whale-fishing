"""Main FastAPI application for Whale Tracker Discord Bot."""
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field

from app.config import config
from app.pricing import price_fetcher
from app.discord_poster import discord_poster
from app.blockchain_monitor import blockchain_monitor

# Configure logging with better readability for systemd journalctl
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    errors = config.validate_config()
    if errors:
        logger.error(f"Configuration errors: {errors}")
        raise RuntimeError(f"Invalid configuration: {', '.join(errors)}")
    
    logger.info("=" * 70)
    logger.info("🚀 WHALE TRACKER BOT STARTING")
    logger.info("=" * 70)
    logger.info(f"Assets: {', '.join(config.supported_assets)}")
    logger.info(f"Threshold: ${config.usd_threshold:,.0f}")
    logger.info(f"Check interval: {config.check_interval}s")
    logger.info("=" * 70)
    
    # Start blockchain monitoring loop
    await blockchain_monitor.start()
    
    yield
    
    # Shutdown
    logger.info("=" * 70)
    logger.info("🛑 WHALE TRACKER BOT STOPPING")
    logger.info("=" * 70)
    await blockchain_monitor.stop()
    await price_fetcher.close()
    await discord_poster.close()


app = FastAPI(
    title="Whale Tracker Discord Bot",
    description="Monitors large crypto transactions and posts alerts to Discord",
    version="1.0.0",
    lifespan=lifespan
)


class WhaleEvent(BaseModel):
    """
    Normalized whale transaction event.
    
    This schema is designed to work with various blockchain data providers.
    Providers should send events in this format, or the endpoint will normalize them.
    """
    asset: str = Field(..., description="Asset symbol (BTC, ETH, XRP, SOL)")
    amount: float = Field(..., description="Amount transferred in native units")
    sender: str = Field(..., description="Sender address")
    receiver: str = Field(..., description="Receiver address")
    tx_hash: str = Field(..., description="Transaction hash")
    value_usd: Optional[float] = Field(None, description="USD value if provided by source")
    timestamp: Optional[int] = Field(None, description="Unix timestamp")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "Whale Tracker Discord Bot",
        "supported_assets": config.supported_assets,
        "usd_threshold": config.usd_threshold
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "discord_configured": bool(config.discord_webhook_url),
        "coingecko_configured": bool(config.coingecko_api_key),
        "supported_assets": config.supported_assets
    }


@app.post("/whale-hook")
async def whale_hook(event: WhaleEvent, request: Request):
    """
    Receive whale transaction events from blockchain data providers.
    
    This endpoint:
    1. Validates the event structure
    2. Checks if asset is supported
    3. Computes USD value if not provided
    4. Filters by USD threshold
    5. Posts qualifying events to Discord
    
    Provider webhook should POST events in WhaleEvent format.
    """
    logger.info(f"Received event: {event.asset} {event.amount} from {event.sender[:16]}...")
    
    # Step 1: Validate asset
    if event.asset not in config.supported_assets:
        logger.warning(f"Unsupported asset: {event.asset}")
        return {
            "status": "ignored",
            "reason": f"Asset {event.asset} not in supported list"
        }
    
    # Step 2: Calculate USD value if not provided
    usd_value = event.value_usd
    if usd_value is None:
        logger.info(f"Computing USD value for {event.amount} {event.asset}")
        usd_value = await price_fetcher.calculate_usd_value(event.asset, event.amount)
        
        if usd_value is None:
            logger.error(f"Failed to compute USD value for {event.asset}")
            return {
                "status": "error",
                "reason": "Could not determine USD value"
            }
    
    # Step 3: Apply threshold filter
    if usd_value < config.usd_threshold:
        logger.debug(
            f"Event below threshold: ${usd_value:,.0f} < ${config.usd_threshold:,.0f}"
        )
        return {
            "status": "ignored",
            "reason": f"Value ${usd_value:,.0f} below threshold ${config.usd_threshold:,.0f}"
        }
    
    # Step 4: Post to Discord
    logger.info(
        f"Whale detected! {event.asset} ${usd_value:,.0f} - Posting to Discord..."
    )
    
    success = await discord_poster.post_whale_alert(
        asset=event.asset,
        amount=event.amount,
        usd_value=usd_value,
        sender=event.sender,
        receiver=event.receiver,
        tx_hash=event.tx_hash
    )
    
    if success:
        return {
            "status": "posted",
            "asset": event.asset,
            "usd_value": usd_value,
            "tx_hash": event.tx_hash
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to post to Discord"
        )


@app.post("/test-alert")
async def test_alert():
    """
    Test endpoint to verify Discord posting works.
    Sends a sample whale alert.
    """
    logger.info("Sending test alert to Discord...")
    
    success = await discord_poster.post_whale_alert(
        asset="BTC",
        amount=25.5,
        usd_value=2500000.00,
        sender="bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
        receiver="bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",
        tx_hash="3a7d8f2e9c1b5a4d6e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d"
    )
    
    if success:
        return {"status": "success", "message": "Test alert posted to Discord"}
    else:
        raise HTTPException(status_code=500, detail="Failed to post test alert")
