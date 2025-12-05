# Whale Tracker Discord Bot - Project Instructions

## Project Overview
FastAPI-based crypto whale transaction monitoring service that posts alerts to Discord.

## Key Components
- `app/main.py`: FastAPI application with `/whale-hook` endpoint
- `app/config.py`: Configuration management with Pydantic
- `app/pricing.py`: CoinGecko price fetching with caching
- `app/discord_poster.py`: Discord webhook posting with retry logic

## Development Guidelines
- Use async/await for all I/O operations
- Log important events (whale detections, errors)
- Never log secrets (webhook URLs, API keys)
- Follow Pydantic models for data validation
- Use tenacity for retry logic on external calls

## Testing
- Use `/test-alert` endpoint to verify Discord integration
- Manual webhook testing with curl/PowerShell
- Check logs for event processing details

## Configuration
All configuration via environment variables in `.env`:
- `DISCORD_WEBHOOK_URL` (required)
- `USD_THRESHOLD` (optional, default: 1000000)
- `COINGECKO_API_KEY` (optional)
- `PRICE_CACHE_TTL` (optional, default: 60)
