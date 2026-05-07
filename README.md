# Momentum-stock-trading

Dependency-free momentum scanner for NASDAQ, NYSE, and AMEX stocks.

## What it does

- Scans supported exchanges for stocks up **10%+ vs. the previous close**
- Confirms the latest **1-hour candle volume is 5x+** the prior 30-day average hourly volume
- Classifies alerts as:
  - `institutional_buy`: price/volume spike with **no substantial recent PR**
  - `retail_pr_momentum`: price/volume spike with a **recent positive PR/news catalyst**
- Avoids alerting the same symbol more than once per UTC day
- Includes:
  - Webull iPhone-friendly universal link
  - Yahoo Finance quote link
  - PR link and short PR summary when available

## Run

```bash
python momentum_alerts.py --format text
```

Useful options:

```bash
python momentum_alerts.py \
  --exchange NASDAQ \
  --limit 100 \
  --state-file .momentum_alert_state.json \
  --format json
```

## Tests

```bash
python -m unittest discover -s tests -v
```
