import asyncio
import time
import os
import requests
import logging
from dotenv import load_dotenv
from datetime import datetime
from agent import get_provider_monitor_data

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger('flare_monitor')

# Default threshold values - can be overridden by environment variables
DEFAULT_THRESHOLDS = {
    "min_availability_6h": 90.0,  # 90%
    "min_availability_24h": 90.0,  # 90%
    "min_success_rate_6h_primary": 20.0,  # 20%
    "min_success_rate_6h_secondary": 85.0,  # 85%
    "min_success_rate_24h_primary": 20.0,  # 20%
    "min_success_rate_24h_secondary": 85.0,  # 85%
}

# Monitoring interval in seconds
DEFAULT_MONITORING_INTERVAL = 15 * 60  # 15 minutes

# Get telegram configuration from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_alert(message):
    """Send an alert message using Telegram bot"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram bot token or chat ID not configured. Cannot send alert.")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Telegram alert sent successfully: {message}")
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")
        return False

def get_thresholds():
    """Get threshold values from environment variables or use defaults"""
    thresholds = {}
    for key, default_value in DEFAULT_THRESHOLDS.items():
        env_value = os.getenv(key.upper())
        thresholds[key] = float(env_value) if env_value else default_value
    return thresholds

async def check_provider_data(custom_provider_address=None):
    """Check provider data against thresholds and send alerts if needed"""
    thresholds = get_thresholds()
    
    try:
        provider_data = await get_provider_monitor_data(custom_provider_address)
        logger.info(f"Provider data retrieved successfully: {provider_data}")
        
        alerts = []
        
        # Check availability thresholds
        if provider_data.availability_6h < thresholds["min_availability_6h"]:
            alerts.append(f"⚠️ 6h Availability is low: {provider_data.availability_6h}% (threshold: {thresholds['min_availability_6h']}%)")
        
        if provider_data.availability_24h < thresholds["min_availability_24h"]:
            alerts.append(f"⚠️ 24h Availability is low: {provider_data.availability_24h}% (threshold: {thresholds['min_availability_24h']}%)")
        
        # Check success rate thresholds
        if provider_data.success_rate_6h.primary < thresholds["min_success_rate_6h_primary"]:
            alerts.append(f"⚠️ 6h Primary Success Rate is low: {provider_data.success_rate_6h.primary}% (threshold: {thresholds['min_success_rate_6h_primary']}%)")
        
        if provider_data.success_rate_6h.secondary < thresholds["min_success_rate_6h_secondary"]:
            alerts.append(f"⚠️ 6h Secondary Success Rate is low: {provider_data.success_rate_6h.secondary}% (threshold: {thresholds['min_success_rate_6h_secondary']}%)")
        
        if provider_data.success_rate_24h.primary < thresholds["min_success_rate_24h_primary"]:
            alerts.append(f"⚠️ 24h Primary Success Rate is low: {provider_data.success_rate_24h.primary}% (threshold: {thresholds['min_success_rate_24h_primary']}%)")
        
        if provider_data.success_rate_24h.secondary < thresholds["min_success_rate_24h_secondary"]:
            alerts.append(f"⚠️ 24h Secondary Success Rate is low: {provider_data.success_rate_24h.secondary}% (threshold: {thresholds['min_success_rate_24h_secondary']}%)")
        
        # Send alerts if any
        if alerts:
            monitored_address = custom_provider_address or os.getenv("PROVIDER_ADDRESS", "Unknown")
            message = f"*FLARE PROVIDER ALERT*\n\nProvider: `{monitored_address}`\n\n" + "\n".join(alerts)
            message += f"\n\n_Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
            send_telegram_alert(message)
            logger.warning(f"Alerts detected: {alerts}")
        else:
            logger.info("All provider metrics are within acceptable thresholds")
        
        return provider_data, alerts
    
    except Exception as e:
        error_message = f"Error checking provider data: {str(e)}"
        logger.error(error_message)
        send_telegram_alert(f"*FLARE PROVIDER MONITOR ERROR*\n\n{error_message}")
        return None, [error_message]

async def monitor_loop():
    """Main monitoring loop that runs at specified intervals"""
    interval = int(os.getenv("MONITORING_INTERVAL", DEFAULT_MONITORING_INTERVAL))
    provider_address = os.getenv("PROVIDER_ADDRESS")
    
    if not provider_address:
        error_msg = "PROVIDER_ADDRESS environment variable is not set!"
        logger.error(error_msg)
        send_telegram_alert(f"*FLARE PROVIDER MONITOR ERROR*\n\n{error_msg}")
        return
        
    logger.info(f"Starting Flare FTSO provider monitoring for address: {provider_address}")
    logger.info(f"Monitoring interval: {interval} seconds")
    
    while True:
        try:
            start_time = time.time()
            await check_provider_data(provider_address)
            
            # Calculate how long to sleep to maintain the desired interval
            elapsed = time.time() - start_time
            sleep_time = max(0, interval - elapsed)
            
            if sleep_time > 0:
                logger.info(f"Waiting {sleep_time:.2f} seconds until next check...")
                await asyncio.sleep(sleep_time)
            else:
                logger.warning(f"Monitor check took {elapsed:.2f}s, longer than the interval ({interval}s)")
        
        except Exception as e:
            logger.error(f"Error in monitor loop: {e}")
            await asyncio.sleep(60)  # Wait a minute if there's an error

async def main():
    """Main entry point"""
    try:
        # Run monitor once on startup
        # await check_provider_data()
        
        # Start continuous monitoring
        await monitor_loop()
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Monitoring terminated due to error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 