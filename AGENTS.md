# Binance Arbitrage Bot — AGENTS.md

## Quick start

```bash
pip install python-binance websockets requests streamlit streamlit-autorefresh
# Edit config.py: set API_KEY, API_SECRET (Binance API credentials)
python get_token.py      # fetch all spot pairs → token.json
python find_pair.py       # discover triangles → triangles.json (rate-limited, ~10s)
python arb.py             # run live arbitrage bot
streamlit run orderbook_dashboard.py  # separate terminal: orderbook viz
```

## Architecture

- **No package manager, no tests, no linting/typecheck.** Pure `.py` scripts in repo root.
- **`arb.py`** is the main entrypoint — connects to Binance WebSocket `@depth5@100ms` streams, computes triangular arbitrage profitability in real-time.
- **`get_token.py`** → `token.json` (cached pair list). **`find_pair.py`** → `triangles.json` (cached arbitrage paths). These are pre-requisite steps before `arb.py`.
- **`orderbook.py`** — `OB` class with asyncio lock for thread-safe orderbook state.
- **`ob.json`** — runtime artifact, auto-saved every 2s by `arb.py`. Consumed by `orderbook_dashboard.py` (Streamlit). Safe to delete at any time.

## Data flow

```
get_token.py → data/token.json → find_pair.py → data/triangles.json → arb.py → data/ob.json
                                                                           ↓
                                                                orderbook_dashboard.py
```

## Key details

- `config.py:FEE_RATE = 0.001` — Binance spot taker fee; edit if your fee tier differs.
- `find_pair.py` has `VOLUME_THRESHOLD = 10_000_000` (USDT pair quote volume filter) and `time.sleep(0.1)` to avoid Binance API rate limits.
- `arb.py` splits symbols into 3 WebSocket groups to stay under Binance's 1024-stream-per-connection limit.
- `triangles.json` can be large (thousands of entries). `arb.py` spawns one coroutine per triangle — this is intentional.
- No `.gitignore` — `ob.json` and `__pycache__/` should be ignored.