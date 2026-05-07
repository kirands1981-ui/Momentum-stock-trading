from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from momentum_alerts import (
    AlertState,
    MomentumSignal,
    NetworkError,
    build_alert,
    build_webull_url,
    load_exchange_symbols,
    parse_latest_signal,
    select_news_match,
)


class FakeClient:
    def __init__(self, text_map=None, json_map=None):
        self.text_map = text_map or {}
        self.json_map = json_map or {}

    def get_text(self, url: str) -> str:
        if url not in self.text_map:
            raise NetworkError(f"Missing text fixture for {url}")
        return self.text_map[url]

    def get_json(self, url: str):
        if url not in self.json_map:
            raise NetworkError(f"Missing json fixture for {url}")
        return self.json_map[url]


class LoadExchangeSymbolsTests(unittest.TestCase):
    def test_load_exchange_symbols_filters_supported_non_etfs(self):
        client = FakeClient(
            text_map={
                "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt": (
                    "Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares\n"
                    "ABCD|ABCD Corp|Q|N|N|100|N|N\n"
                    "QQQ|Invesco ETF|Q|N|N|100|Y|N\n"
                    "TEST|Test Issue|Q|Y|N|100|N|N\n"
                    "File Creation Time: now\n"
                ),
                "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt": (
                    "ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol\n"
                    "XYZ|XYZ Inc|N|XYZ|N|100|N|XYZ\n"
                    "AMX|AMEX Name|A|AMX|N|100|N|AMX\n"
                    "ETF1|ETF Name|N|ETF1|Y|100|N|ETF1\n"
                    "File Creation Time: now\n"
                ),
            }
        )

        symbols = load_exchange_symbols(client)

        self.assertEqual(
            [(item.symbol, item.exchange) for item in symbols],
            [("AMX", "AMEX"), ("ABCD", "NASDAQ"), ("XYZ", "NYSE")],
        )


class ParseLatestSignalTests(unittest.TestCase):
    def test_parse_latest_signal_returns_matching_signal(self):
        timestamps = [1_700_000_000 + (index * 3600) for index in range(31)]
        closes = [10.0] * 30 + [11.5]
        volumes = [100.0] * 30 + [800.0]
        payload = {
            "chart": {
                "result": [
                    {
                        "meta": {"chartPreviousClose": 10.0},
                        "timestamp": timestamps,
                        "indicators": {"quote": [{"close": closes, "volume": volumes}]},
                    }
                ]
            }
        }

        signal = parse_latest_signal("ABCD", "NASDAQ", payload)

        self.assertIsNotNone(signal)
        self.assertAlmostEqual(signal.price_change_pct, 15.0)
        self.assertAlmostEqual(signal.relative_volume, 8.0)

    def test_parse_latest_signal_rejects_non_matching_signal(self):
        timestamps = [1_700_000_000 + (index * 3600) for index in range(31)]
        closes = [10.0] * 30 + [10.4]
        volumes = [100.0] * 30 + [300.0]
        payload = {
            "chart": {
                "result": [
                    {
                        "meta": {"chartPreviousClose": 10.0},
                        "timestamp": timestamps,
                        "indicators": {"quote": [{"close": closes, "volume": volumes}]},
                    }
                ]
            }
        }

        self.assertIsNone(parse_latest_signal("ABCD", "NASDAQ", payload))


class NewsClassificationTests(unittest.TestCase):
    def test_select_news_match_prefers_positive_recent_pr(self):
        signal_time = datetime(2026, 5, 7, 15, 0, tzinfo=UTC)
        news = [
            {
                "title": "ABCD announces major distribution partnership",
                "publisher": "Business Wire",
                "providerPublishTime": int(datetime(2026, 5, 7, 13, 0, tzinfo=UTC).timestamp()),
                "link": "https://example.com/pr",
                "summary": "ABCD announced a new revenue-generating distribution partnership.",
            },
            {
                "title": "ABCD stock chat room mentions momentum",
                "publisher": "Forum",
                "providerPublishTime": int(datetime(2026, 5, 7, 12, 0, tzinfo=UTC).timestamp()),
                "link": "https://example.com/forum",
            },
        ]

        match = select_news_match(news, signal_time)

        self.assertIsNotNone(match)
        self.assertEqual(match.url, "https://example.com/pr")
        self.assertIn("distribution partnership", match.summary)

    def test_build_alert_marks_institutional_when_no_pr(self):
        signal = MomentumSignal(
            symbol="ABCD",
            exchange="NASDAQ",
            latest_price=11.2,
            previous_close=10.0,
            price_change_pct=12.0,
            latest_volume=600000.0,
            avg_hourly_volume_30d=100000.0,
            relative_volume=6.0,
            candle_end_utc="2026-05-07T15:00:00+00:00",
        )

        alert = build_alert(signal, None)

        self.assertEqual(alert.classification, "institutional_buy")
        self.assertIsNone(alert.pr_link)
        self.assertIn("silent accumulation", alert.alert_reason)


class StateAndLinkTests(unittest.TestCase):
    def test_alert_state_deduplicates_by_day(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            state_path = Path(tmp_dir) / "state.json"
            state = AlertState(state_path)
            state.mark_alerted("ABCD", "2026-05-07")
            state.save()

            reloaded = AlertState(state_path)
            self.assertTrue(reloaded.already_alerted("ABCD", "2026-05-07"))
            self.assertFalse(reloaded.already_alerted("ABCD", "2026-05-08"))

    def test_build_webull_url_uses_exchange_prefix(self):
        self.assertEqual(
            build_webull_url("NASDAQ", "ABCD"),
            "https://www.webull.com/quote/nasdaq-abcd",
        )


if __name__ == "__main__":
    unittest.main()
