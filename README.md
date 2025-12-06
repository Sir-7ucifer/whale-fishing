# 🐋 Whale Tracker Discord Bot

A real-time crypto whale transaction monitoring system that automatically detects large transfers across Bitcoin (BTC), Ethereum (ETH), XRP, and Solana (SOL) networks and posts instant alerts to Discord. Runs continuously with configurable check intervals and supports buy/sell/transfer classification.

## Features

- **Multi-Chain Support**: Monitors BTC, ETH, XRP, and SOL networks simultaneously
- **Automatic Monitoring**: Continuous polling of blockchain explorers (1-minute intervals by default)
- **Configurable Threshold**: Set custom USD value thresholds (default: $1,000,000+)
- **Transaction Classification**: Automatically detects buy/sell/transfer activity with exchange identification
- **Real-Time Alerts**: Posts color-coded embeds to Discord (🟢 buy, 🔴 sell, 🟠 transfer)
- **Free APIs Only**: Uses public blockchain explorers (Etherscan, Blockchain.info, XRP Scan, Solscan)
- **Automatic USD Pricing**: Fetches live prices from CoinGecko with 60-second cache
- **Retry Logic**: Reliable Discord posting with exponential backoff (3 attempts)
- **Block Explorer Links**: Direct links to transactions on chain-specific explorers
- **Ubuntu Auto-Start**: Systemd service for 24/7 operation with auto-restart on failure

## Architecture

```text
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
- Optional: CoinGecko Pro API key (for higher rate limits; free tier works fine)

### 2. Installation

```powershell
# Navigate to project directory
cd whale-fishing

# Create virtual environment
python3 -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create `.env` file in the project root:

```env
# REQUIRED: Your Discord webhook URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN

# Optional: Adjust USD threshold (default: $1,000,000)
USD_THRESHOLD=1000000

# Optional: CoinGecko Pro API key (default: free tier)
COINGECKO_API_KEY=

# Optional: Check interval in seconds (default: 60)
CHECK_INTERVAL=60

# Optional: Price cache TTL in seconds (default: 60)
PRICE_CACHE_TTL=60
```

### 4. Run the Service

**Windows (Development):**

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start the server (includes auto-monitoring)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Ubuntu (Production with Auto-Start):**

```bash
# Make setup script executable
chmod +x setup-autostart.sh

# Run setup (installs systemd service)
sudo ./setup-autostart.sh

# Bot will start automatically and persist on reboot!
```

The service will start on `http://localhost:8000` and begin automatic monitoring.

### 5. Verify Setup

Check application startup logs:

```text
Application startup complete
Found 0 whale transactions above $1,000,000
Waiting 60 seconds until next check...
```

Send a test alert to verify Discord integration:

```powershell
curl -X POST http://localhost:8000/test-alert
```

You should see a whale alert in your Discord channel immediately! 🎉

## API Endpoints

### `GET /` or `GET /health`

Health check endpoint - returns service status and configuration.

**Response:**

```json
{
  "status": "running",
  "config": {
    "assets": ["BTC", "ETH", "XRP", "SOL"],
    "usd_threshold": 1000000,
    "check_interval": 60
  }
}
```

### `POST /test-alert`

Sends a sample whale alert to Discord for verification.

**Response:**

```json
{
  "status": "posted",
  "message": "Test alert sent to Discord"
}
```

### `POST /whale-hook` (Deprecated)

Legacy endpoint for manual webhook testing (not used for automatic monitoring).

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

## Blockchain Data Sources

The bot uses **free, public blockchain explorers** and automatically polls them every CHECK_INTERVAL seconds (default: 60 seconds). No external data provider configuration needed!

### Supported Networks & Data Sources

| Network | Data Source | API | Rate Limit | Coverage |
| --------- | ------------ | ----- | ----------- | ---------- |
| **Bitcoin (BTC)** | Blockchain.info | Free API | 1 req/sec | Last 10 transactions |
| **Ethereum (ETH)** | Etherscan | Free API | 5 calls/sec | USDT transfers (latest block) |
| **XRP (XRP)** | XRP Scan | Free API | Unlimited | Payment transactions |
| **Solana (SOL)** | Solscan | Free API | Unlimited | Latest transactions |

### How It Works

1. **Startup**: Bot starts and initializes configuration
2. **Monitoring Loop**: Every 60 seconds, bot fetches latest transactions from each blockchain
3. **Filtering**: Transactions below USD_THRESHOLD are ignored
4. **Classification**: Each transaction is analyzed for buy/sell/transfer type
5. **Discord Alert**: Highest-valued transaction is posted to Discord with color coding
6. **Repeat**: Process continues indefinitely

### Testing Alerts Manually

You can test the Discord integration with:

```powershell
curl -X POST http://localhost:8000/test-alert
```

Or trigger the monitoring loop manually:

```powershell
curl -X GET http://localhost:8000/health
```

## Configuration Details

### Environment Variables

| Variable | Required | Default | Description |
| ---------- | ---------- | --------- | ------------- |
| `DISCORD_WEBHOOK_URL` | ✅ Yes | - | Discord webhook URL for posting alerts |
| `USD_THRESHOLD` | ❌ No | 1000000 | Minimum USD value to trigger alert |
| `CHECK_INTERVAL` | ❌ No | 60 | Seconds between blockchain checks |
| `COINGECKO_API_KEY` | ❌ No | - | CoinGecko API key (free tier works) |
| `PRICE_CACHE_TTL` | ❌ No | 60 | Seconds to cache price data |

### Supported Assets

| Asset | Symbol | Explorer | Data Source |
| ------- | -------- | ---------- | ------------- |
| Bitcoin | BTC | blockchain.com | Blockchain.info API |
| Ethereum | ETH | etherscan.io | Etherscan API |
| Ripple | XRP | xrpscan.com | XRP Scan API |
| Solana | SOL | solscan.io | Solscan API |

### Known Exchange Addresses

The bot automatically identifies transactions involving these exchanges:

- Binance (multiple wallets)
- Coinbase
- Kraken
- OKX
- Bybit
- Crypto.com
- Bitfinex
- Gate.io
- Huobi
- Kucoin
- Gemini
- ... and more

**Transaction Type Indicators:**

- 🟢 **Buy**: Whale receiving from exchange
- 🔴 **Sell**: Whale sending to exchange
- 🟠 **Transfer**: Non-exchange address interactions

## Discord Alert Format

Alerts are posted as color-coded rich embeds:

**Buy Alert (Green 🟢):**

```text
📈 Whale BOUGHT 25.5 BTC!
Value: $2,500,000
From: Binance (0x123...)
To: Unknown Whale
Tx: [View on Explorer]
```

**Sell Alert (Red 🔴):**

```text
📉 Whale SOLD 50 ETH!
Value: $1,500,000
From: Unknown Whale
To: Coinbase (0x456...)
Tx: [View on Explorer]
```

**Transfer Alert (Orange 🟠):**

```text
🔄 Whale TRANSFERRED 1000 XRP
Value: $1,200,000
From: 0x789...
To: 0xABC...
Tx: [View on Explorer]
```

Each alert includes:

- Emoji indicator (📈 buy, 📉 sell, 🔄 transfer)
- Asset symbol and amount
- USD value (formatted with commas)
- Sender & receiver addresses
- Clickable link to block explorer

## Production Deployment

### Ubuntu Server (Recommended)

The bot includes automated setup for Ubuntu servers:

```bash
# 1. Transfer project to Ubuntu server
scp -r whale-fishing ubuntu@your-server:/home/ubuntu/

# 2. SSH into server and setup environment
ssh ubuntu@your-server
cd whale-fishing
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure .env
nano .env  # Add DISCORD_WEBHOOK_URL

# 4. Run auto-start setup
chmod +x setup-autostart.sh
sudo ./setup-autostart.sh
```

The bot will now:

- ✅ Start automatically on server boot
- ✅ Restart automatically if it crashes
- ✅ Run 24/7 without SSH session needed
- ✅ Log to systemd journal (view with `sudo journalctl -u whale-tracker -f`)

**Manage the service:**

```bash
sudo systemctl status whale-tracker     # Check status
sudo systemctl stop whale-tracker       # Stop bot
sudo systemctl restart whale-tracker    # Restart bot
sudo systemctl disable whale-tracker    # Disable auto-start
```

### Docker

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

```bash
docker build -t whale-tracker .
docker run -p 8000:8000 --env-file .env whale-tracker
```

### Security Considerations

- **Secrets**: Never commit `.env` file to git - it's already in `.gitignore`
- **Webhook URL**: Keep Discord webhook URL secret (don't share in public repositories)
- **API Keys**: Store CoinGecko API key securely in environment variables
- **HTTPS**: Use HTTPS when exposing bot to internet
- **Firewall**: Restrict port 8000 access if not needed publicly
- **Logging**: The bot avoids logging sensitive data (webhook URLs, API keys)

## Troubleshooting

### Bot starts but no alerts appear

1. **Verify Discord webhook URL:**

   ```bash
   curl -X POST http://localhost:8000/test-alert
   ```

   You should see a test alert in Discord.

2. **Check logs for errors:**

   ```bash
   # Windows
   # Look at terminal output

   # Ubuntu (systemd)
   sudo journalctl -u whale-tracker -n 50
   ```

3. **Verify monitoring loop is running:**
   - Logs should show "Found X whale transactions" every CHECK_INTERVAL seconds
   - Most checks will report "Found 0 whale transactions" if no $1M+ moves occurred

### "Configuration errors: DISCORD_WEBHOOK_URL is required"

```bash
# Create .env file
nano .env

# Add your Discord webhook URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN
```

### Blockchain API errors

- **Etherscan**: Check internet connectivity and rate limits (5 calls/sec)
- **Blockchain.info**: Verify BTC network is online
- **XRP Scan**: Ensure XRP Ledger is responding
- **Solscan**: Check Solana network status

The bot will skip failed API calls and retry on next interval.

### High USD_THRESHOLD showing no alerts

- Increase sensitivity by lowering USD_THRESHOLD in `.env`
- Check blockchain explorer directly for transactions
- Verify CoinGecko pricing is working: `curl https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd`

### Service won't start on Ubuntu

```bash
# Check for errors
sudo systemctl status whale-tracker
sudo journalctl -u whale-tracker -n 100

# Verify port isn't in use
sudo lsof -i :8000

# Check permissions
sudo chown -R www-data:www-data /home/ubuntu/whale-fishing
```

## Project Structure

```text
whale-fishing/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app + monitoring loop
│   ├── config.py                # Configuration & asset definitions
│   ├── pricing.py               # CoinGecko price fetching with cache
│   ├── discord_poster.py        # Discord webhook integration
│   ├── blockchain_monitor.py    # Multi-chain transaction fetchers
│   └── address_identifier.py    # Exchange detection & tx classification
├── requirements.txt             # Python dependencies
├── .env                         # Configuration (user-created)
├── .env.template               # Config template (reference)
├── setup-autostart.sh          # Ubuntu systemd setup script
├── whale-tracker.service       # Systemd service unit
├── UBUNTU-SETUP.md            # Ubuntu deployment guide
├── README.md                   # This file
└── .gitignore                  # Git ignore rules
```

### Module Overview

| Module | Purpose |
| -------- | --------- |
| `main.py` | FastAPI app with lifespan management, routes, monitoring loop |
| `config.py` | Pydantic-based configuration loading from `.env` |
| `pricing.py` | CoinGecko API client with in-memory TTL cache |
| `discord_poster.py` | Discord webhook posting with retry logic (tenacity) |
| `blockchain_monitor.py` | Parallel fetchers for BTC/ETH/XRP/SOL transaction data |
| `address_identifier.py` | Exchange address database & buy/sell/transfer classification |

## Development

### Local Testing

```powershell
# Activate environment
.\venv\Scripts\Activate.ps1

# Run with auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Test health check
curl http://localhost:8000/health

# Test alert
curl -X POST http://localhost:8000/test-alert
```

### Modifying Thresholds or Intervals

Edit `.env`:

```env
USD_THRESHOLD=500000        # Alert on $500k+ instead of $1M
CHECK_INTERVAL=30           # Check every 30 seconds instead of 60
PRICE_CACHE_TTL=120         # Cache prices for 2 minutes
```

## Possible Enhancements

- Add more blockchains (Cardano, Polygon, Bitcoin Cash, etc.)
- Lower or tiered USD thresholds for different alerts
- Database persistence for transaction history
- Web dashboard showing recent whale activity
- Telegram bot integration alongside Discord
- SMS alerts for critical transactions
- Machine learning for anomaly detection
- Whale address tracking and profiling

## License

MIT License - feel free to use and modify for your needs.

## Support

For issues or questions:

- Check the **Troubleshooting** section above
- Review **Logs**:
  - Windows: Terminal output
  - Ubuntu: `sudo journalctl -u whale-tracker -f`
- Verify **.env configuration** is correct
- Test with `/test-alert` endpoint

---

**Built with:** FastAPI • CoinGecko • Etherscan • Blockchain.info • Discord Webhooks

**Monitors:** Bitcoin (BTC) • Ethereum (ETH) • Ripple (XRP) • Solana (SOL)

**Deploys on:** Windows • Linux/Ubuntu • Docker

🐋 Happy whale tracking! 🚀
