# 🐋 Whale Tracker Discord Bot

A real-time crypto whale transaction monitoring system that detects large transfers across Bitcoin (BTC), Ethereum (ETH), XRP, and Solana (SOL) and posts instant alerts to Discord.

## Features

- **Multi-Chain Support**: Monitors BTC, ETH, XRP, and SOL networks
- **Configurable Threshold**: Set custom USD value thresholds (default: $1,000,000+)
- **Real-Time Alerts**: Posts structured alerts to Discord via webhook
- **Automatic USD Valuation**: Fetches current prices from CoinGecko with caching
- **Retry Logic**: Reliable Discord posting with exponential backoff
- **Block Explorer Links**: Direct links to transactions on chain-specific explorers
- **Easy Integration**: Simple webhook endpoint for blockchain data providers

## Architecture

```
┌─────────────────────┐
│ Blockchain Data     │
│ Provider (Webhook)  │
└──────────┬──────────┘
           │ POST /whale-hook
           ▼
┌─────────────────────┐
│  FastAPI Service    │
│  - Event validation │
│  - USD computation  │
│  - Threshold filter │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Discord Webhook     │
│ (Formatted Alert)   │
└─────────────────────┘
```

## Quick Start

### 1. Prerequisites

- Python 3.11 or higher
- A Discord webhook URL ([Create one](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks))
- Blockchain data provider account (see [Providers](#blockchain-data-providers) below)

### 2. Installation

```powershell
# Clone or download this repository
cd whale-tracker-discord-bot

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Copy `.env.template` to `.env` and configure:

```powershell
cp .env.template .env
```

Edit `.env`:

```env
# REQUIRED: Your Discord webhook URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN

# Optional: Adjust threshold (default: $1,000,000)
USD_THRESHOLD=1000000

# Optional: CoinGecko Pro API key for higher rate limits
COINGECKO_API_KEY=
```

### 4. Run the Service

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The service will start on `http://localhost:8000`

### 5. Test the Setup

Send a test alert to verify Discord integration:

```powershell
curl -X POST http://localhost:8000/test-alert
```

You should see a whale alert in your Discord channel! 🎉

## API Endpoints

### `POST /whale-hook`

Receives whale transaction events from blockchain data providers.

**Request Body:**

```json
{
  "asset": "BTC",
  "amount": 25.5,
  "sender": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
  "receiver": "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",
  "tx_hash": "3a7d8f2e9c1b5a4d6e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d",
  "value_usd": 2500000.00,
  "timestamp": 1701619200
}
```

**Fields:**
- `asset` (required): Asset symbol - must be BTC, ETH, XRP, or SOL
- `amount` (required): Amount transferred in native units
- `sender` (required): Sender address
- `receiver` (required): Receiver address
- `tx_hash` (required): Transaction hash
- `value_usd` (optional): USD value - if not provided, will be computed using current price
- `timestamp` (optional): Unix timestamp

**Response:**

```json
{
  "status": "posted",
  "asset": "BTC",
  "usd_value": 2500000.0,
  "tx_hash": "3a7d8f2e9c1b5a4d..."
}
```

### `GET /`

Health check endpoint - returns service status and configuration.

### `GET /health`

Detailed health check with configuration validation.

### `POST /test-alert`

Sends a test whale alert to Discord for verification.

## Blockchain Data Providers

To receive real-time whale transactions, you need to connect a blockchain data provider to the `/whale-hook` endpoint. Here are recommended providers:

### Option 1: Whale Alert API
- Website: https://whale-alert.io
- Supports: BTC, ETH, XRP, SOL and many more
- Configure their webhook to POST to your `/whale-hook` endpoint
- They provide pre-filtered large transactions

### Option 2: Alchemy Notify
- Website: https://www.alchemy.com/notify
- Supports: ETH, SOL (via separate APIs)
- Set up address activity webhooks for known whale addresses
- Configure custom webhook URL to your service

### Option 3: QuickNode Streams
- Website: https://www.quicknode.com/streams
- Supports: ETH, SOL, and others
- Create a stream filtered by transaction value
- Configure webhook destination to `/whale-hook`

### Option 4: Tatum Notifications
- Website: https://tatum.io
- Supports: BTC, ETH, SOL, and more
- Set up webhook notifications for large transactions
- Point webhook to your service endpoint

### Manual Testing

For development and testing, you can manually POST events:

```powershell
# Test a whale transaction
curl -X POST http://localhost:8000/whale-hook `
  -H "Content-Type: application/json" `
  -d '{
    "asset": "ETH",
    "amount": 1000.0,
    "sender": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "receiver": "0x1234567890123456789012345678901234567890",
    "tx_hash": "0xabc123def456...",
    "value_usd": 3500000.00
  }'
```

## Configuration Details

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_WEBHOOK_URL` | Yes | - | Discord webhook URL for posting alerts |
| `USD_THRESHOLD` | No | 1000000 | Minimum USD value to trigger alert |
| `COINGECKO_API_KEY` | No | - | CoinGecko Pro API key (optional, for higher rate limits) |
| `PRICE_CACHE_TTL` | No | 60 | Price cache TTL in seconds |

### Supported Assets

| Asset | Symbol | Block Explorer |
|-------|--------|----------------|
| Bitcoin | BTC | blockchain.com |
| Ethereum | ETH | etherscan.io |
| Ripple | XRP | xrpscan.com |
| Solana | SOL | solscan.io |

## Discord Alert Format

Alerts are posted as rich embeds with the following information:

- 🐋 **Title**: "Whale Alert Detected"
- **Asset**: Symbol (BTC, ETH, XRP, SOL)
- **Amount**: Formatted with token symbol
- **USD Value**: Formatted with commas (e.g., $1,250,000)
- **From**: Abbreviated sender address
- **To**: Abbreviated receiver address
- **Transaction**: Clickable link to block explorer

## Production Deployment

### Using Docker (Recommended)

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY .env .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```powershell
docker build -t whale-tracker .
docker run -p 8000:8000 --env-file .env whale-tracker
```

### Exposing to Internet

For blockchain providers to reach your webhook:

1. **ngrok** (Development):
   ```powershell
   ngrok http 8000
   ```
   Use the provided HTTPS URL as your webhook endpoint.

2. **Cloud Deployment** (Production):
   - Deploy to Azure App Service, AWS Lambda, Google Cloud Run, or similar
   - Ensure `/whale-hook` endpoint is publicly accessible via HTTPS
   - Update your blockchain provider's webhook configuration with your public URL

### Security Considerations

- **Authentication**: Add webhook signature verification for production
- **Rate Limiting**: Implement rate limiting on `/whale-hook`
- **HTTPS**: Always use HTTPS in production
- **Secrets**: Never commit `.env` file - use environment variables or secrets manager
- **Logging**: Avoid logging sensitive data (webhook URLs, API keys)

## Troubleshooting

### "Configuration errors: DISCORD_WEBHOOK_URL is required"

Set your Discord webhook URL in `.env`:
```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### No alerts appearing in Discord

1. Verify webhook URL is correct
2. Test with `/test-alert` endpoint
3. Check application logs for errors
4. Verify Discord channel permissions

### "Failed to compute USD value"

- Check CoinGecko API status
- Verify internet connectivity
- Consider adding `COINGECKO_API_KEY` for higher rate limits

### Events being ignored

- Check logs for "below threshold" or "unsupported asset" messages
- Verify `USD_THRESHOLD` configuration
- Ensure asset symbol matches exactly (BTC, ETH, XRP, SOL)

## Development

### Running Tests

```powershell
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Structure

```
whale-tracker-discord-bot/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── pricing.py           # Price fetching and caching
│   └── discord_poster.py    # Discord webhook integration
├── requirements.txt
├── .env.template
└── README.md
```

## Contributing

Contributions welcome! Areas for improvement:

- Additional blockchain support (Cardano, Polygon, etc.)
- Webhook signature verification
- Database persistence for event history
- Web dashboard for monitoring
- Additional alert destinations (Telegram, Slack, etc.)

## License

MIT License - feel free to use and modify for your needs.

## Support

For issues or questions:
- Check the troubleshooting section above
- Review application logs (`uvicorn` output)
- Verify your blockchain provider's webhook configuration

---

Built with FastAPI, CoinGecko, and Discord Webhooks 🚀
