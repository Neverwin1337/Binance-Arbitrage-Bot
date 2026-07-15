# Binance Arbitrage Bot — Refactor Design

## Goal

Refactor the 5 flat Python scripts into a maintainable package structure with type hints, logging, error handling, and batch triangle scanning — no new features, no behavioral changes.

## Directory Layout

```
root/
  arbitrage/
    __init__.py
    config.py          # API_KEY, API_SECRET, FEE_RATE, VOLUME_THRESHOLD, etc.
    exchange.py        # Binance REST API calls (exchange info, 24hr ticker)
    orderbook.py       # OB class — thread-safe orderbook state
    scanner.py         # Triangle discovery logic (from find_pair.py)
    arb.py             # Main loop: WebSocket + batch triangle scan
    logger.py          # Centralized logging setup
  scripts/
    run.py             # Entry point: python scripts/run.py
    run_dashboard.py   # Entry point: streamlit run scripts/run_dashboard.py
    get_token.py       # Fetch token list (thin wrapper)
    find_pair.py       # Find triangles (thin wrapper)
  data/
    token.json         # Symbol groupings (output of get_token)
    triangles.json     # Discovered triangles (output of find_pair)
    ob.json            # Orderbook snapshots (runtime artifact)
  config.py            # Backward-compat: re-exports from arbitrage.config
  get_token.py         # Backward-compat: delegates to arbitrage.exchange
  find_pair.py         # Backward-compat: delegates to arbitrage.scanner
  orderbook.py         # Backward-compat: re-exports OB
  orderbook_dashboard.py  # Backward-compat: delegates to scripts/run_dashboard
  arb.py               # Backward-compat: delegates to scripts/run
  docs/
    superpowers/specs/2026-07-15-arbitrage-bot-refactor-design.md
```

## Module Breakdown

### `arbitrage/config.py`
- `API_KEY`, `API_SECRET` from env vars or config.py
- `FEE_RATE = 0.001`
- `VOLUME_THRESHOLD = 10_000_000`
- `WS_GROUP_COUNT = 3`
- `LOG_LEVEL = "INFO"`
- All env-var-overridable (e.g., `BINANCE_API_KEY`, `BINANCE_API_SECRET`)

### `arbitrage/exchange.py`
- `fetch_symbol_groups() -> dict[str, list[str]]` — calls Binance exchangeInfo, groups by quote asset (USDT, USDC, BNB, BTC, ETH)
- `fetch_24hr_volumes(symbols: set[str]) -> dict[str, float]` — calls /ticker/24hr for each symbol with rate limiting
- Uses `requests` (sync) for simplicity, matching current approach

### `arbitrage/orderbook.py`
- `OB` class with instance-level `orderbooks: dict[str, TickerData]`
- `update_orderbook(symbol, bids, asks)` — async, acquires lock, stores best bid/ask + amounts
- `get_ticker(symbol) -> Optional[TickerData]` — returns None if symbol unknown
- `TickerData = TypedDict` with bid/ask/amount fields

### `arbitrage/scanner.py`
- `discover_triangles(data_path: str = "data")` — reads token.json, fetches 24hr volumes, enumerates all 3-coin combos, applies volume filter, writes triangles.json
- Same algorithm as current `find_pair.py` but:
  - Type hints on all functions
  - Logging instead of print
  - Rate-limit handling logged
  - Skip invalid symbols gracefully

### `arbitrage/arb.py`
- `ArbBot` class encapsulating all state:
  - `orderbook: OB`
  - `triangles: list[dict]`
  - `symbol_groups: list[list[str]]`
- `run()` method that:
  1. Loads triangles.json
  2. Collects all symbols, splits into WS groups
  3. Launches WebSocket listeners for each group
  4. Launches periodic ob.json saver (every 2s)
  5. Launches single `scan_loop()` instead of per-triangle coroutines

#### Scan Loop (replaces per-triangle coroutines)
```python
async def scan_loop(self):
    while True:
        for tri in self.triangles:
            s1, s2, s3 = tri["symbols"]
            # figure out which legs are USDT, which is cross
            # fetch prices from orderbook
            # compute p1, p2
            # log if > 1
        await asyncio.sleep(0.2)
```
This replaces `len(triangles)` coroutines with one loop. The 0.2s sleep per full cycle matches the current per-coroutine sleep but is far simpler and avoids O(n) task overhead.

### `arbitrage/logger.py`
- `setup_logger(name: str) -> logging.Logger`
- Console handler with format: `[2026-07-15 12:34:56] [INFO] [arb] message`
- Uses `logging` stdlib module

### Backward-Compat Root Scripts
- Root `config.py` → `from arbitrage.config import *`
- Root `orderbook.py` → `from arbitrage.orderbook import OB`
- Root `arb.py` → `from scripts.run import main`
- Root `get_token.py` → `from scripts.get_token import main`
- Root `find_pair.py` → `from scripts.find_pair import main`
- Root `orderbook_dashboard.py` → unchanged (standalone Streamlit)

## Changes from Current Code

| Aspect | Current | After |
|--------|---------|-------|
| Structure | 5 flat .py files | `arbitrage/` package + `scripts/` entry points |
| Imports | Top-level `open()`, `json.load()` at module scope | All imports inside functions, no side effects |
| Triangle scanning | 1 coroutine per triangle (potentially 1000s) | Single batch loop |
| Logging | `print()` | `logging.Logger` with timestamps |
| Type hints | None | Full type hints |
| Error handling | Bare `except: print(e); break` | Specific handling + reconnect logic |
| Globals | `global first`, module-level `orderbook` | Instance state in `ArbBot` |
| Orderbook state | Class-level dict (shared across instances) | Instance-level dict |
| WebSocket reconnect | None | Reconnect on failure |

## What Stays the Same
- Arbitrage detection formulas (p1, p2 calculations)
- `get_ab_direction()` logic
- Fee rate application
- 3 WebSocket groups (1024 streams per connection limit)
- Streamlit dashboard
- `ob.json` format
- `token.json` / `triangles.json` schemas
- Console output (via logger instead of print, but visible by default)

## Non-Goals
- No trade execution
- No alerts/notifications
- No pip-installable packaging
- No test framework
- No config file format changes