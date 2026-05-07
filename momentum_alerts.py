#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
YAHOO_QUOTE_URL = "https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbols}"
YAHOO_CHART_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    "?interval=1h&range=30d&includePrePost=false"
)
YAHOO_NEWS_URL = (
    "https://query1.finance.yahoo.com/v1/finance/search"
    "?q={symbol}&quotesCount=1&newsCount={news_count}&enableFuzzyQuery=false"
)
DEFAULT_STATE_FILE = ".momentum_alert_state.json"
DEFAULT_NEWS_COUNT = 8
PRICE_SPIKE_THRESHOLD = 10.0
RELATIVE_VOLUME_THRESHOLD = 5.0
MIN_HISTORY_BARS = 30
SUPPORTED_EXCHANGES = ("NASDAQ", "NYSE", "AMEX")
POSITIVE_PR_KEYWORDS = (
    "announce",
    "approval",
    "award",
    "beat",
    "buyback",
    "collaboration",
    "contract",
    "earnings",
    "expands",
    "fda",
    "guidance",
    "launch",
    "merger",
    "partnership",
    "phase",
    "positive",
    "receives",
    "report",
    "secures",
    "signs",
    "surge",
    "upgrade",
    "wins",
)
NEGATIVE_PR_KEYWORDS = (
    "bankruptcy",
    "delisting",
    "dilution",
    "investigation",
    "lawsuit",
    "miss",
    "offering",
    "reverse split",
)
PRESS_RELEASE_SOURCES = (
    "accesswire",
    "business wire",
    "globenewswire",
    "newsfile",
    "pr newswire",
)
EXCHANGE_TO_WEBULL = {
    "NASDAQ": "nasdaq",
    "NYSE": "nyse",
    "AMEX": "amex",
}


class NetworkError(RuntimeError):
    pass


@dataclass(frozen=True)
class SymbolRecord:
    symbol: str
    exchange: str


@dataclass(frozen=True)
class PriceSnapshot:
    symbol: str
    exchange: str
    regular_market_price: float
    previous_close: float
    change_percent: float


@dataclass(frozen=True)
class MomentumSignal:
    symbol: str
    exchange: str
    latest_price: float
    previous_close: float
    price_change_pct: float
    latest_volume: float
    avg_hourly_volume_30d: float
    relative_volume: float
    candle_end_utc: str


@dataclass(frozen=True)
class NewsMatch:
    url: str
    title: str
    summary: str
    publisher: str
    published_at_utc: str | None


@dataclass(frozen=True)
class MomentumAlert:
    symbol: str
    exchange: str
    classification: str
    alert_reason: str
    latest_price: float
    previous_close: float
    price_change_pct: float
    latest_volume: float
    avg_hourly_volume_30d: float
    relative_volume: float
    candle_end_utc: str
    webull_url: str
    yahoo_finance_url: str
    pr_link: str | None
    pr_summary: str


class HttpJsonClient:
    def __init__(self, timeout: int = 20) -> None:
        self.timeout = timeout

    def get_json(self, url: str) -> dict[str, Any]:
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 MomentumStockTrading/1.0",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.load(response)
        except (HTTPError, URLError, TimeoutError) as exc:
            raise NetworkError(f"Failed to fetch {url}: {exc}") from exc

    def get_text(self, url: str) -> str:
        request = Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 MomentumStockTrading/1.0"},
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError) as exc:
            raise NetworkError(f"Failed to fetch {url}: {exc}") from exc


class AlertState:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.data = self._load()

    def _load(self) -> dict[str, list[str]]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def already_alerted(self, symbol: str, on_date: str) -> bool:
        return symbol.upper() in set(self.data.get(on_date, []))

    def mark_alerted(self, symbol: str, on_date: str) -> None:
        symbols = set(self.data.get(on_date, []))
        symbols.add(symbol.upper())
        self.data[on_date] = sorted(symbols)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2, sort_keys=True), encoding="utf-8")


def parse_pipe_table(text: str) -> list[dict[str, str]]:
    rows = [line.strip() for line in text.splitlines() if line.strip()]
    if not rows:
        return []
    header = rows[0].split("|")
    parsed: list[dict[str, str]] = []
    for row in rows[1:]:
        if row.startswith("File Creation Time"):
            continue
        columns = row.split("|")
        if len(columns) != len(header):
            continue
        parsed.append({header[i].strip(): columns[i].strip() for i in range(len(header))})
    return parsed


def load_exchange_symbols(
    client: HttpJsonClient,
    exchanges: Iterable[str] = SUPPORTED_EXCHANGES,
    limit: int | None = None,
) -> list[SymbolRecord]:
    selected = {exchange.upper() for exchange in exchanges}
    symbols: list[SymbolRecord] = []

    if "NASDAQ" in selected:
        nasdaq_rows = parse_pipe_table(client.get_text(NASDAQ_LISTED_URL))
        for row in nasdaq_rows:
            if row.get("Test Issue") != "N" or row.get("ETF") == "Y":
                continue
            symbols.append(SymbolRecord(symbol=row["Symbol"], exchange="NASDAQ"))

    if selected.intersection({"NYSE", "AMEX"}):
        other_rows = parse_pipe_table(client.get_text(OTHER_LISTED_URL))
        exchange_map = {"N": "NYSE", "A": "AMEX"}
        for row in other_rows:
            exchange_code = row.get("Exchange")
            exchange = exchange_map.get(exchange_code or "")
            if exchange not in selected:
                continue
            if row.get("Test Issue") != "N" or row.get("ETF") == "Y":
                continue
            symbols.append(SymbolRecord(symbol=row["ACT Symbol"], exchange=exchange))

    deduped: dict[str, SymbolRecord] = {}
    for record in symbols:
        deduped.setdefault(record.symbol.upper(), SymbolRecord(record.symbol.upper(), record.exchange))

    ordered = sorted(deduped.values(), key=lambda item: (item.exchange, item.symbol))
    return ordered[:limit] if limit else ordered


def chunked(values: list[str], size: int) -> Iterable[list[str]]:
    for index in range(0, len(values), size):
        yield values[index : index + size]


def fetch_price_snapshots(
    client: HttpJsonClient,
    symbols: list[SymbolRecord],
    batch_size: int = 150,
) -> list[PriceSnapshot]:
    exchange_by_symbol = {item.symbol.upper(): item.exchange for item in symbols}
    snapshots: list[PriceSnapshot] = []

    for batch in chunked([item.symbol for item in symbols], batch_size):
        joined = ",".join(batch)
        url = YAHOO_QUOTE_URL.format(symbols=quote(joined, safe=","))
        payload = client.get_json(url)
        for item in payload.get("quoteResponse", {}).get("result", []):
            symbol = str(item.get("symbol", "")).upper()
            exchange = exchange_by_symbol.get(symbol)
            price = item.get("regularMarketPrice")
            previous_close = item.get("regularMarketPreviousClose")
            if not exchange or price in (None, 0) or previous_close in (None, 0):
                continue
            change_percent = ((float(price) - float(previous_close)) / float(previous_close)) * 100
            snapshots.append(
                PriceSnapshot(
                    symbol=symbol,
                    exchange=exchange,
                    regular_market_price=float(price),
                    previous_close=float(previous_close),
                    change_percent=change_percent,
                )
            )
    return snapshots


def parse_latest_signal(symbol: str, exchange: str, chart_payload: dict[str, Any]) -> MomentumSignal | None:
    result = ((chart_payload.get("chart") or {}).get("result") or [None])[0]
    if not result:
        return None

    quote = (((result.get("indicators") or {}).get("quote") or [None])[0]) or {}
    timestamps = result.get("timestamp") or []
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []
    previous_close = float((result.get("meta") or {}).get("chartPreviousClose") or 0)
    if previous_close <= 0:
        previous_close = float((result.get("meta") or {}).get("previousClose") or 0)
    if previous_close <= 0:
        return None

    candles = [
        (ts, close, volume)
        for ts, close, volume in zip(timestamps, closes, volumes)
        if ts is not None and close is not None and volume not in (None, 0)
    ]
    if len(candles) < MIN_HISTORY_BARS + 1:
        return None

    latest_timestamp, latest_close, latest_volume = candles[-1]
    prior_volumes = [float(volume) for _, _, volume in candles[:-1]]
    avg_volume = sum(prior_volumes) / len(prior_volumes)
    if avg_volume <= 0:
        return None

    relative_volume = float(latest_volume) / avg_volume
    price_change_pct = ((float(latest_close) - previous_close) / previous_close) * 100

    if relative_volume < RELATIVE_VOLUME_THRESHOLD or price_change_pct < PRICE_SPIKE_THRESHOLD:
        return None

    candle_end = datetime.fromtimestamp(int(latest_timestamp), tz=UTC).isoformat()
    return MomentumSignal(
        symbol=symbol,
        exchange=exchange,
        latest_price=float(latest_close),
        previous_close=previous_close,
        price_change_pct=price_change_pct,
        latest_volume=float(latest_volume),
        avg_hourly_volume_30d=avg_volume,
        relative_volume=relative_volume,
        candle_end_utc=candle_end,
    )


def fetch_signal_for_snapshot(client: HttpJsonClient, snapshot: PriceSnapshot) -> MomentumSignal | None:
    url = YAHOO_CHART_URL.format(symbol=quote(snapshot.symbol))
    payload = client.get_json(url)
    return parse_latest_signal(snapshot.symbol, snapshot.exchange, payload)


def normalize_news_summary(item: dict[str, Any]) -> str:
    raw_summary = (
        item.get("summary")
        or item.get("description")
        or item.get("snippet")
        or item.get("shortSummary")
        or ""
    )
    cleaned = " ".join(str(raw_summary).split())
    if cleaned:
        return cleaned
    title = " ".join(str(item.get("title") or "").split())
    publisher = str(item.get("publisher") or item.get("providerName") or "Recent news")
    return f"{publisher}: {title}".strip()


def is_substantial_positive_pr(item: dict[str, Any]) -> bool:
    text = " ".join(
        str(value or "").lower()
        for value in (
            item.get("title"),
            item.get("summary"),
            item.get("description"),
            item.get("snippet"),
            item.get("publisher"),
            item.get("providerName"),
        )
    )
    if any(keyword in text for keyword in NEGATIVE_PR_KEYWORDS):
        return False
    if any(keyword in text for keyword in POSITIVE_PR_KEYWORDS):
        return True
    return any(source in text for source in PRESS_RELEASE_SOURCES) and "announce" in text


def select_news_match(
    news_items: list[dict[str, Any]],
    signal_time: datetime,
    lookback_hours: int = 48,
) -> NewsMatch | None:
    lower_bound = signal_time - timedelta(hours=lookback_hours)
    candidates: list[tuple[datetime | None, dict[str, Any]]] = []
    for item in news_items:
        published_epoch = item.get("providerPublishTime") or item.get("pubDate")
        published_at: datetime | None = None
        if isinstance(published_epoch, (int, float)):
            published_at = datetime.fromtimestamp(int(published_epoch), tz=UTC)
            if published_at < lower_bound or published_at > signal_time:
                continue
        candidates.append((published_at, item))

    ordered = sorted(candidates, key=lambda pair: pair[0] or lower_bound, reverse=True)
    for published_at, item in ordered:
        if not is_substantial_positive_pr(item):
            continue
        link = (
            item.get("link")
            or item.get("clickThroughUrl", {}).get("url")
            or item.get("canonicalUrl", {}).get("url")
        )
        if not link:
            continue
        summary = normalize_news_summary(item)
        return NewsMatch(
            url=str(link),
            title=str(item.get("title") or ""),
            summary=summary,
            publisher=str(item.get("publisher") or item.get("providerName") or ""),
            published_at_utc=published_at.isoformat() if published_at else None,
        )
    return None


def build_webull_url(exchange: str, symbol: str) -> str:
    market = EXCHANGE_TO_WEBULL.get(exchange.upper(), exchange.lower())
    return f"https://www.webull.com/quote/{market}-{symbol.lower()}"


def build_alert(signal: MomentumSignal, news_match: NewsMatch | None) -> MomentumAlert:
    if news_match:
        classification = "retail_pr_momentum"
        reason = "Positive recent PR/news matches the volume and price spike."
        pr_link = news_match.url
        pr_summary = news_match.summary
    else:
        classification = "institutional_buy"
        reason = "No substantial recent PR found; spike looks more like silent accumulation."
        pr_link = None
        pr_summary = "No substantial recent PR was found in Yahoo Finance news results."

    return MomentumAlert(
        symbol=signal.symbol,
        exchange=signal.exchange,
        classification=classification,
        alert_reason=reason,
        latest_price=signal.latest_price,
        previous_close=signal.previous_close,
        price_change_pct=signal.price_change_pct,
        latest_volume=signal.latest_volume,
        avg_hourly_volume_30d=signal.avg_hourly_volume_30d,
        relative_volume=signal.relative_volume,
        candle_end_utc=signal.candle_end_utc,
        webull_url=build_webull_url(signal.exchange, signal.symbol),
        yahoo_finance_url=f"https://finance.yahoo.com/quote/{signal.symbol}",
        pr_link=pr_link,
        pr_summary=pr_summary,
    )


def fetch_news_match(client: HttpJsonClient, symbol: str, candle_end_utc: str) -> NewsMatch | None:
    url = YAHOO_NEWS_URL.format(symbol=quote(symbol), news_count=DEFAULT_NEWS_COUNT)
    payload = client.get_json(url)
    news_items = payload.get("news") or []
    signal_time = datetime.fromisoformat(candle_end_utc)
    return select_news_match(news_items, signal_time=signal_time)


def scan_market(
    client: HttpJsonClient,
    exchanges: Iterable[str],
    state: AlertState,
    limit: int | None = None,
    max_workers: int = 12,
) -> list[MomentumAlert]:
    symbols = load_exchange_symbols(client, exchanges=exchanges, limit=limit)
    if not symbols:
        return []

    snapshots = fetch_price_snapshots(client, symbols)
    candidate_snapshots = [
        snapshot for snapshot in snapshots if snapshot.change_percent >= PRICE_SPIKE_THRESHOLD
    ]

    alerts: list[MomentumAlert] = []
    today = datetime.now(tz=UTC).date().isoformat()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(fetch_signal_for_snapshot, client, snapshot): snapshot
            for snapshot in candidate_snapshots
        }
        for future in as_completed(future_map):
            snapshot = future_map[future]
            try:
                signal = future.result()
            except NetworkError as exc:
                print(f"Skipping {snapshot.symbol}: {exc}", file=sys.stderr)
                continue
            if not signal or state.already_alerted(signal.symbol, today):
                continue
            try:
                news_match = fetch_news_match(client, signal.symbol, signal.candle_end_utc)
            except NetworkError as exc:
                print(f"News lookup failed for {signal.symbol}: {exc}", file=sys.stderr)
                news_match = None
            alert = build_alert(signal, news_match)
            alerts.append(alert)
            state.mark_alerted(signal.symbol, today)

    state.save()
    return sorted(alerts, key=lambda item: (-item.price_change_pct, -item.relative_volume, item.symbol))


def format_text_alert(alert: MomentumAlert) -> str:
    lines = [
        f"{alert.symbol} ({alert.exchange}) - {alert.classification}",
        f"  Reason: {alert.alert_reason}",
        f"  Price: {alert.latest_price:.2f} vs prev close {alert.previous_close:.2f} ({alert.price_change_pct:.2f}%)",
        f"  Volume: {alert.latest_volume:.0f} vs 30d hourly avg {alert.avg_hourly_volume_30d:.0f} ({alert.relative_volume:.2f}x)",
        f"  Candle end (UTC): {alert.candle_end_utc}",
        f"  Webull: {alert.webull_url}",
        f"  Yahoo Finance: {alert.yahoo_finance_url}",
        f"  PR Link: {alert.pr_link or 'None'}",
        f"  PR Summary: {alert.pr_summary}",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Scan NASDAQ, NYSE, and AMEX symbols for 1-hour price/volume spikes and classify "
            "them as silent institutional accumulation or PR-driven retail momentum."
        )
    )
    parser.add_argument(
        "--exchange",
        dest="exchanges",
        action="append",
        choices=SUPPORTED_EXCHANGES,
        help="Limit the scan to a specific exchange. Can be passed multiple times.",
    )
    parser.add_argument("--limit", type=int, help="Limit the symbol universe for a smaller scan.")
    parser.add_argument(
        "--state-file",
        default=DEFAULT_STATE_FILE,
        help="JSON file used to avoid duplicate same-day alerts.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=12,
        help="Maximum concurrent Yahoo Finance chart lookups.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output alerts as JSON or plain text.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    exchanges = args.exchanges or list(SUPPORTED_EXCHANGES)
    client = HttpJsonClient()
    state = AlertState(Path(args.state_file))

    try:
        alerts = scan_market(
            client=client,
            exchanges=exchanges,
            state=state,
            limit=args.limit,
            max_workers=args.max_workers,
        )
    except NetworkError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps([asdict(alert) for alert in alerts], indent=2))
    else:
        print("\n\n".join(format_text_alert(alert) for alert in alerts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
