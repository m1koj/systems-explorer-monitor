# Flare FTSO Provider Monitoring System

Automated monitoring system for Flare FTSO providers that scrapes metrics from the Systems Explorer and sends alerts when values fall below thresholds.

## Quick Start with Docker (Recommended)

The simplest way to run this monitor is using Docker:

```bash
# Clone the repository
git clone https://github.com/yourusername/systems-explorer-monitor.git
cd systems-explorer-monitor

# Configure your environment variables
cp .env.example .env
# Edit .env with your provider address and OpenAI API key

# Build the Docker image
docker build -t flare-ftso-monitor .

# Run the container
docker run -d --name ftso-monitor \
  --restart unless-stopped \
  --env-file .env \
  flare-ftso-monitor
```

### Monitoring Container Status

```bash
# Check container status
docker ps -a | grep ftso-monitor

# View logs
docker logs -f ftso-monitor
```

## Configuration

Required environment variables in `.env`:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `PROVIDER_ADDRESS` | Your FTSO provider address |

Optional configuration:

| Variable | Description | Default |
|----------|-------------|---------|
| `NETWORK` | Network name (flare, songbird, etc.) | flare |
| `TELEGRAM_BOT_TOKEN` | Bot token for alerts | - |
| `TELEGRAM_CHAT_ID` | Chat ID for alerts | - |
| `MONITORING_INTERVAL` | Check interval in seconds | 900 (15min) |
| `MIN_AVAILABILITY_6H` | Minimum 6h availability % | 90.0 |
| `MIN_AVAILABILITY_24H` | Minimum 24h availability % | 90.0 |
| `MIN_SUCCESS_RATE_6H_PRIMARY` | Min 6h primary success % | 20.0 |
| `MIN_SUCCESS_RATE_6H_SECONDARY` | Min 6h secondary success % | 85.0 |
| `MIN_SUCCESS_RATE_24H_PRIMARY` | Min 24h primary success % | 20.0 |
| `MIN_SUCCESS_RATE_24H_SECONDARY` | Min 24h secondary success % | 85.0 |

## Manual Installation (Alternative)

If you prefer not to use Docker:

1. Ensure Python 3.11+ is installed
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install --with-deps chromium
   ```
3. Configure `.env` file
4. Run with `python main.py`

## Troubleshooting

- **No alerts received**: Verify Telegram bot configuration
- **Browser errors**: Ensure Playwright is properly installed
- **API errors**: Check your OpenAI API key