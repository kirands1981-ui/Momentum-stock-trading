"""
Scheduler Module - Runs scanner at regular intervals during market hours
Optional: Use this to run automated scans
"""

import schedule
import time
import logging
from datetime import datetime
from pytz import timezone
import pytz
from config import CHECK_INTERVAL_SECONDS, MARKET_OPEN_HOUR, MARKET_CLOSE_HOUR
from scanner import MomentumScanner

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# US Eastern Time
ET = timezone('US/Eastern')


class MarketScheduler:
    """Manages automated scanning during market hours"""

    def __init__(self, check_interval_seconds: int = CHECK_INTERVAL_SECONDS):
        self.check_interval = check_interval_seconds
        self.scanner = MomentumScanner()
        self.is_running = False

    def is_market_open(self) -> bool:
        """Check if US stock market is currently open"""
        now = datetime.now(ET)
        
        # Check if weekday (Mon-Fri)
        if now.weekday() >= 5:  # Saturday=5, Sunday=6
            return False
        
        # Check if during market hours (9:30 AM - 4:00 PM ET)
        market_open_time = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close_time = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open_time <= now <= market_close_time

    def run_scan(self):
        """Run one scan cycle"""
        if not self.is_market_open():
            logger.debug("Market is closed, skipping scan")
            return

        try:
            logger.info("Starting scheduled scan...")
            results = self.scanner.scan_all_exchanges()
            
            logger.info(f"Scan complete: {results['total_momentum']} momentum signals found")
        except Exception as e:
            logger.error(f"Error during scheduled scan: {e}", exc_info=True)

    def schedule_scans(self):
        """Schedule scans at regular intervals"""
        # Schedule scan every CHECK_INTERVAL_SECONDS during market hours
        interval_minutes = max(1, self.check_interval // 60)
        
        schedule.every(interval_minutes).minutes.do(self.run_scan)
        
        logger.info(f"Scheduler initialized: scanning every {interval_minutes} minutes during market hours")

    def start(self):
        """Start the scheduler"""
        self.is_running = True
        self.schedule_scans()
        
        logger.info("Momentum scanner scheduler started")
        logger.info(f"Scanning every {self.check_interval} seconds during market hours")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            self.is_running = False

    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        logger.info("Scheduler stopped")


def run_scheduler():
    """Main entry point for scheduler"""
    scheduler = MarketScheduler()
    scheduler.start()


if __name__ == "__main__":
    run_scheduler()
