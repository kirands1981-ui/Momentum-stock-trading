import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd

import scanner
from data_fetcher import StockDataFetcher


class FakeTicker:
    @property
    def fast_info(self):
        raise RuntimeError("rate limited")

    @property
    def news(self):
        raise RuntimeError("rate limited")

    def history(self, period="1d", interval="1h"):
        return pd.DataFrame()


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FinnhubFallbackTests(unittest.TestCase):
    def test_get_stock_data_uses_finnhub_when_yahoo_is_empty(self):
        fetcher = StockDataFetcher()
        fetcher.finnhub_api_key = "test-key"
        candle_payload = {
            "s": "ok",
            "o": [100.0, 101.0],
            "h": [101.0, 112.0],
            "l": [99.0, 100.0],
            "c": [101.0, 111.5],
            "v": [1200, 5400],
            "t": [1715100000, 1715103600],
        }

        with patch("data_fetcher.yf.Ticker", return_value=FakeTicker()):
            fetcher.session.get = Mock(return_value=FakeResponse(candle_payload))
            frame = fetcher.get_stock_data("AAPL", period="5d")

        self.assertIsNotNone(frame)
        self.assertEqual(["Open", "High", "Low", "Close", "Volume"], list(frame.columns))
        self.assertEqual(2, len(frame))
        self.assertEqual(111.5, float(frame["Close"].iloc[-1]))


class DryRunTests(unittest.TestCase):
    def test_run_dry_run_writes_alert_outputs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            alerts_path = tmp_path / "alerts.json"
            history_path = tmp_path / "alert_history.json"
            log_path = tmp_path / "momentum.log"
            chart_path = tmp_path / "chart.png"

            with patch.object(scanner, "OUTPUT_ALERT_FILE", str(alerts_path)), \
                 patch.object(scanner, "ALERT_HISTORY_FILE", str(history_path)), \
                 patch.object(scanner, "LOG_FILE", str(log_path)), \
                 patch.object(scanner, "create_momentum_chart", return_value=str(chart_path)), \
                 patch.object(scanner.MomentumScanner, "_send_notifications", return_value=None):
                momentum_scanner = scanner.MomentumScanner()
                result = momentum_scanner.run_dry_run()

            self.assertTrue(result["momentum_detected"])
            self.assertIn(result["buy_type"], ("INSTITUTIONAL_ACCUMULATION", "BREAKOUT_BUY", "RETAIL_BUY"))
            self.assertTrue(alerts_path.exists())
            self.assertTrue(history_path.exists())

            alerts = json.loads(alerts_path.read_text())
            history = json.loads(history_path.read_text())

            self.assertEqual("DRYRUN", alerts[0]["ticker"])
            self.assertIn(history["DRYRUN"]["buy_type"], ("INSTITUTIONAL_ACCUMULATION", "BREAKOUT_BUY", "RETAIL_BUY"))


if __name__ == "__main__":
    unittest.main()
