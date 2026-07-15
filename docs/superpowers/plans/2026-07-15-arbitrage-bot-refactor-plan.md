# Binance Arbitrage Bot Refactor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor 5 flat Python scripts into a maintainable `arbitrage/` package with type hints, logging, error handling, and batch triangle scanning.

**Architecture:** Single `arbitrage/` package (not pip-installable) with `scripts/` entry points. Root scripts become backward-compat wrappers. No new features.

**Tech Stack:** Python 3.10+, `requests`, `websockets`, `python-binance`, `streamlit`, `streamlit-autorefresh`

## Global Constraints

- No new features, no behavioral changes to arbitrage detection formulas
- No test framework added
- `ob.json` format must remain identical
- `token.json` / `triangles.json` schemas must remain identical
- Console output must remain visible (via logger instead of print)
- Root scripts must remain runnable as before (`python arb.py`, `python get_token.py`, etc.)

---

### Task 1: Create directory structure and `__init__.py`

**Files:**
- Create: `arbitrage/__init__.py`
- Create: `scripts/` (directory)

**Interfaces:**
- Consumes: nothing
- Produces: package directory structure

- [ ] **Step 1: Create directories**

```bash
mkdir -p arbitrage scripts data
```

- [ ] **Step 2: Write `arbitrage/__init__.py`**

```python
```

---

### Task 2: `arbitrage/config.py` — Configuration

**Files:**
- Create: `arbitrage/config.py`

**Interfaces:**
- Consumes: nothing
- Produces: `FEE_RATE`, `VOLUME_THRESHOLD`, `WS_GROUP_COUNT`, `LOG_LEVEL`, `API_KEY`, `API_SECRET`, `DATA_DIR`

- [ ] **Step 1: Write `arbitrage/config.py`**

```python
import os

API_KEY = os.environ.get("BINANCE_API_KEY", "")
API_SECRET = os.environ.get("BINANCE_API_SECRET", "")
FEE_RATE = float(os.environ.get("BINANCE_FEE_RATE", "0.001"))
VOLUME_THRESHOLD = int(os.environ.get("BINANCE_VOLUME_THRESHOLD", "10000000"))
WS_GROUP_COUNT = int(os.environ.get("BINANCE_WS_GROUP_COUNT", "3"))
LOG_LEVEL = os.environ.get("BINANCE_LOG_LEVEL", "INFO")
DATA_DIR = os.environ.get("BINANCE_DATA_DIR", "data")
```

---

### Task 3: `arbitrage/logger.py` — Logging setup

**Files:**
- Create: `arbitrage/logger.py`

**Interfaces:**
- Consumes: `LOG_LEVEL` from config
- Produces: `setup_logger(name: str) -> logging.Logger`

- [ ] **Step 1: Write `arbitrage/logger.py`**

```python
import logging
import sys
from arbitrage.config import LOG_LEVEL


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(LOG_LEVEL)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
```

---

### Task 4: `arbitrage/orderbook.py` — OB class with type hints

**Files:**
- Create: `arbitrage/orderbook.py`

**Interfaces:**
- Consumes: nothing
- Produces: `class OB`, `TickerData TypedDict`
  - `OB.update_orderbook(symbol: str, bids: list[list[str]], asks: list[list[str]]) -> None`
  - `OB.get_ticker(symbol: str) -> TickerData | None`

- [ ] **Step 1: Write `arbitrage/orderbook.py`**

```python
import asyncio
from typing import TypedDict, Optional


class TickerData(TypedDict):
    bid: float
    bid_amount: float
    ask: float
    ask_amount: float


class OB:
    def __init__(self) -> None:
        self.orderbooks: dict[str, TickerData] = {}
        self._lock = asyncio.Lock()

    async def update_orderbook(
        self, symbol: str, bids: list[list[str]], asks: list[list[str]]
    ) -> None:
        async with self._lock:
            best_bid = float(bids[0][0]) if bids else None
            best_bid_amount = float(bids[0][1]) if bids else None
            best_ask = float(asks[0][0]) if asks else None
            best_ask_amount = float(asks[0][1]) if asks else None
            self.orderbooks[symbol] = TickerData(
                bid=best_bid,
                bid_amount=best_bid_amount,
                ask=best_ask,
                ask_amount=best_ask_amount,
            )

    async def get_ticker(self, symbol: str) -> Optional[TickerData]:
        return self.orderbooks.get(symbol)
```

---

### Task 5: `arbitrage/exchange.py` — Binance REST API calls

**Files:**
- Create: `arbitrage/exchange.py`

**Interfaces:**
- Consumes: `API_KEY`, `API_SECRET`, `DATA_DIR` from config
- Produces: `fetch_symbol_groups() -> dict[str, list[str]]`, `fetch_24hr_volumes(symbols: set[str]) -> dict[str, float]`

- [ ] **Step 1: Write `arbitrage/exchange.py`**

```python
import json
import time
from typing import Optional

import requests
from binance.client import Client

from arbitrage.config import API_KEY, API_SECRET, DATA_DIR
from arbitrage.logger import setup_logger

logger = setup_logger("exchange")


def fetch_symbol_groups() -> dict[str, list[str]]:
    client = Client(API_KEY, API_SECRET)
    exchange_info = client.get_exchange_info()
    symbols = exchange_info["symbols"]

    spot_symbols = [
        s["symbol"]
        for s in symbols
        if s["status"] == "TRADING" and s["isSpotTradingAllowed"]
    ]

    groups: dict[str, list[str]] = {
        "usdt": [],
        "usdc": [],
        "bnb": [],
        "btc": [],
        "eth": [],
    }

    for sym in spot_symbols:
        if sym[-4:] == "USDT":
            groups["usdt"].append(sym)
        elif sym[-4:] == "USDC":
            groups["usdc"].append(sym)
        elif sym[-3:] == "BNB":
            groups["bnb"].append(sym)
        elif sym[-3:] == "BTC":
            groups["btc"].append(sym)
        elif sym[-3:] == "ETH":
            groups["eth"].append(sym)

    token_path = f"{DATA_DIR}/token.json"
    with open(token_path, "w") as f:
        json.dump(groups, f)
    logger.info("Wrote %d symbol groups to %s", len(groups), token_path)
    return groups


def fetch_24hr_volumes(symbols: set[str]) -> dict[str, float]:
    url = "https://api.binance.com/api/v3/ticker/24hr"
    volumes: dict[str, float] = {}
    for symbol in symbols:
        try:
            resp = requests.get(url, params={"symbol": symbol}, timeout=10)
            if resp.status_code == 200:
                t = resp.json()
                volumes[symbol] = float(t.get("quoteVolume", 0))
            else:
                volumes[symbol] = 0.0
                logger.warning("Failed to fetch volume for %s: HTTP %d", symbol, resp.status_code)
        except Exception as e:
            volumes[symbol] = 0.0
            logger.error("Error fetching volume for %s: %s", symbol, e)
        time.sleep(0.1)
    return volumes
```

---

### Task 6: `arbitrage/scanner.py` — Triangle discovery

**Files:**
- Create: `arbitrage/scanner.py`

**Interfaces:**
- Consumes: `fetch_24hr_volumes`, `VOLUME_THRESHOLD`, `DATA_DIR`
- Produces: `discover_triangles() -> list[dict]`

- [ ] **Step 1: Write `arbitrage/scanner.py`**

```python
import json
from itertools import combinations

from arbitrage.config import VOLUME_THRESHOLD, DATA_DIR
from arbitrage.exchange import fetch_24hr_volumes
from arbitrage.logger import setup_logger

logger = setup_logger("scanner")


def _get_pair_symbol(a: str, b: str, all_symbols: set[str]) -> str | None:
    if a + b in all_symbols:
        return a + b
    if b + a in all_symbols:
        return b + a
    return None


def discover_triangles() -> list[dict]:
    token_path = f"{DATA_DIR}/token.json"
    with open(token_path, "r") as f:
        data = json.load(f)

    all_symbols: set[str] = set()
    for group in data.values():
        all_symbols.update(group)

    logger.info("Fetching 24hr volumes for %d symbols...", len(all_symbols))
    symbol_volume_map = fetch_24hr_volumes(all_symbols)

    assets: set[str] = set()
    for pair in all_symbols:
        if len(pair) > 6 and pair[-4:] in ("USDT", "USDC"):
            base = pair[:-4]
            quote = pair[-4:]
        else:
            base = pair[:-3]
            quote = pair[-3:]
        assets.add(base)
        assets.add(quote)

    triangles: list[dict] = []
    for a, b, c in combinations(assets, 3):
        ab = _get_pair_symbol(a, b, all_symbols)
        bc = _get_pair_symbol(b, c, all_symbols)
        ca = _get_pair_symbol(c, a, all_symbols)
        if not (ab and bc and ca):
            continue

        usdt_vol_ok = True
        for sym in (ab, bc, ca):
            if "USDT" in sym and symbol_volume_map.get(sym, 0) < VOLUME_THRESHOLD:
                usdt_vol_ok = False
                break
        if usdt_vol_ok:
            triangles.append({
                "route": (a, b, c),
                "symbols": (ab, bc, ca),
            })

    triangles_path = f"{DATA_DIR}/triangles.json"
    with open(triangles_path, "w") as f:
        json.dump(triangles, f)
    logger.info("Found %d triangles, saved to %s", len(triangles), triangles_path)
    return triangles
```

---

### Task 7: `arbitrage/arb.py` — Main ArbBot class with batch scan loop

**Files:**
- Create: `arbitrage/arb.py`

**Interfaces:**
- Consumes: `OB`, `config`, `logger`
- Produces: `class ArbBot` with `run()` method

- [ ] **Step 1: Write `arbitrage/arb.py`**

```python
import json
import asyncio

import websockets

from arbitrage.config import FEE_RATE, WS_GROUP_COUNT, DATA_DIR
from arbitrage.orderbook import OB
from arbitrage.logger import setup_logger

logger = setup_logger("arb")


def get_ab_direction(s1: str, s2: str, s3: str) -> bool:
    s1 = s1.replace("/", "").upper()
    s2 = s2.replace("/", "").upper()
    s3 = s3.replace("/", "").upper()

    a = s1.replace("USDT", "")
    b = s2.replace("USDT", "")

    if not ("USD" in s1 and "USD" in s2):
        raise ValueError(f"Invalid pair: {s1}, {s2} must contain USDT")

    if s3 == a + b:
        return True
    if s3 == b + a:
        return False
    raise ValueError(f"Invalid cross pair: {s3}, expected {a+b} or {b+a}")


class ArbBot:
    def __init__(self) -> None:
        self.orderbook = OB()
        self.triangles: list[dict] = []

    def load_triangles(self) -> None:
        path = f"{DATA_DIR}/triangles.json"
        with open(path, "r") as f:
            self.triangles = json.load(f)
        logger.info("Loaded %d triangles from %s", len(self.triangles), path)

    def _build_symbol_groups(self) -> list[list[str]]:
        all_symbols: list[str] = []
        seen: set[str] = set()
        for tri in self.triangles:
            for s in tri["symbols"]:
                sl = s.lower()
                if sl not in seen:
                    seen.add(sl)
                    all_symbols.append(sl)

        group_size = len(all_symbols) // WS_GROUP_COUNT
        if len(all_symbols) % WS_GROUP_COUNT:
            group_size += 1
        groups = [
            all_symbols[i * group_size : (i + 1) * group_size]
            for i in range(WS_GROUP_COUNT)
        ]
        return [g for g in groups if g]

    async def _handle_depth_message(self, msg: str) -> None:
        data = json.loads(msg)
        if "data" in data:
            stream = data["stream"]
            symbol = stream.replace("@depth5@100ms", "").upper()
            stream_data = data["data"]
            bids = stream_data["bids"]
            asks = stream_data["asks"]
            await self.orderbook.update_orderbook(symbol, bids, asks)

    async def _listen_ws(self, symbols: list[str]) -> None:
        streams = [f"{s}@depth5@100ms" for s in symbols]
        url = f"wss://stream.binance.com:9443/stream?streams={'/'.join(streams)}"
        while True:
            try:
                async with websockets.connect(url) as ws:
                    async for msg in ws:
                        asyncio.create_task(self._handle_depth_message(msg))
            except Exception as e:
                logger.error("WebSocket disconnected: %s. Reconnecting in 5s...", e)
                await asyncio.sleep(5)

    async def _scan_loop(self) -> None:
        while True:
            for tri in self.triangles:
                s1, s2, s3 = tri["symbols"]
                try:
                    if "USDT" not in s1:
                        direction = get_ab_direction(s2, s3, s1)
                        u1, u2, cross = (s2, s3, s1) if direction else (s3, s2, s1)
                    elif "USDT" not in s2:
                        direction = get_ab_direction(s1, s3, s2)
                        u1, u2, cross = (s1, s3, s2) if direction else (s3, s1, s2)
                    else:
                        direction = get_ab_direction(s1, s2, s3)
                        u1, u2, cross = (s1, s2, s3) if direction else (s2, s1, s3)

                    t1 = await self.orderbook.get_ticker(u1)
                    t2 = await self.orderbook.get_ticker(u2)
                    tc = await self.orderbook.get_ticker(cross)
                    if t1 is None or t2 is None or tc is None:
                        continue

                    p1 = ((tc["bid"] * t2["bid"]) / t1["ask"]) * ((1 - FEE_RATE) ** 3)
                    p2 = (t1["bid"] / (t2["ask"] * tc["ask"])) * ((1 - FEE_RATE) ** 3)

                    if p1 > 1:
                        logger.info("Profit: %s -> %s -> %s : %.6f", u1, cross, u2, p1)
                    elif p2 > 1:
                        logger.info("Profit: %s -> %s -> %s : %.6f", u2, cross, u1, p2)
                except Exception as e:
                    logger.debug("Scan error for %s: %s", tri["symbols"], e)

            await asyncio.sleep(0.2)

    async def _periodic_save(self, interval: int = 2) -> None:
        while True:
            path = f"{DATA_DIR}/ob.json"
            with open(path, "w") as f:
                json.dump(self.orderbook.orderbooks, f)
            await asyncio.sleep(interval)

    async def run(self) -> None:
        self.load_triangles()
        groups = self._build_symbol_groups()
        logger.info("Starting %d WebSocket groups", len(groups))

        tasks = [
            self._listen_ws(group) for group in groups
        ] + [
            self._scan_loop(),
            self._periodic_save(),
        ]

        await asyncio.gather(*tasks)
```

---

### Task 8: `scripts/run.py` — Entry point for the arb bot

**Files:**
- Create: `scripts/run.py`

**Interfaces:**
- Consumes: `ArbBot`
- Produces: `main()` function

- [ ] **Step 1: Write `scripts/run.py`**

```python
import asyncio
from arbitrage.arb import ArbBot


async def main() -> None:
    bot = ArbBot()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
```

---

### Task 9: `scripts/get_token.py` and `scripts/find_pair.py` — Entry points

**Files:**
- Create: `scripts/get_token.py`
- Create: `scripts/find_pair.py`

**Interfaces:**
- Produces: `main()` functions

- [ ] **Step 1: Write `scripts/get_token.py`**

```python
from arbitrage.exchange import fetch_symbol_groups


def main() -> None:
    fetch_symbol_groups()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Write `scripts/find_pair.py`**

```python
from arbitrage.scanner import discover_triangles


def main() -> None:
    discover_triangles()


if __name__ == "__main__":
    main()
```

---

### Task 10: `scripts/run_dashboard.py` — Entry point for dashboard

**Files:**
- Create: `scripts/run_dashboard.py`

**Interfaces:**
- Produces: `main()` function

- [ ] **Step 1: Write `scripts/run_dashboard.py`**

```python
import json

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from arbitrage.config import DATA_DIR

st_autorefresh(interval=1000)
st.set_page_config(page_title="Orderbook Dashboard", layout="wide")
st.title("币安盘口可视化 (Orderbook Dashboard)")


def load_orderbooks() -> dict:
    path = f"{DATA_DIR}/ob.json"
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        st.warning(f"读取{path}失败: {e}")
        return {}


orderbooks = load_orderbooks()
symbols = sorted(orderbooks.keys())

selected = st.selectbox("选择交易对 (symbol)", symbols)

if selected and selected in orderbooks:
    ob = orderbooks[selected]
    st.subheader(f"盘口 - {selected}")
    st.table({
        "买一价(bid)": [ob["bid"]],
        "买一量(bid_amount)": [ob.get("bid_amount", "")],
        "卖一价(ask)": [ob["ask"]],
        "卖一量(ask_amount)": [ob.get("ask_amount", "")],
    })

st.markdown("---")
st.subheader("全部交易对盘口快照")
st.dataframe([
    {
        "symbol": sym,
        "bid": ob["bid"],
        "bid_amount": ob["bid_amount"],
        "ask": ob["ask"],
        "ask_amount": ob["ask_amount"],
    }
    for sym, ob in orderbooks.items()
])

st.info("本页面每次刷新会重新读取ob.json。可用Streamlit的自动刷新插件实现自动刷新。")


def main() -> None:
    pass
```

---

### Task 11: Root backward-compat wrappers

**Files:**
- Modify: `config.py`
- Modify: `orderbook.py`
- Modify: `arb.py`
- Modify: `get_token.py`
- Modify: `find_pair.py`
- Modify: `orderbook_dashboard.py`

**Interfaces:**
- Must preserve existing import behavior (`from config import API_KEY`, `from orderbook import OB`, etc.)

- [ ] **Step 1: Rewrite `config.py`**

```python
from arbitrage.config import API_KEY, API_SECRET, FEE_RATE
```

- [ ] **Step 2: Rewrite `orderbook.py`**

```python
from arbitrage.orderbook import OB
```

- [ ] **Step 3: Rewrite `arb.py`**

```python
from scripts.run import main

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

- [ ] **Step 4: Rewrite `get_token.py`**

```python
from scripts.get_token import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Rewrite `find_pair.py`**

```python
from scripts.find_pair import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Rewrite `orderbook_dashboard.py`**

```python
from scripts.run_dashboard import main
```

---

### Task 12: Verify everything runs

**Files:**
- None

- [ ] **Step 1: Verify imports work**

```bash
cd /mnt/c/Users/Public/Documents/Binance-Arbitrage-Bot
python -c "from arbitrage.config import API_KEY, FEE_RATE; print('config OK')"
python -c "from arbitrage.logger import setup_logger; print('logger OK')"
python -c "from arbitrage.orderbook import OB; print('orderbook OK')"
python -c "from arbitrage.exchange import fetch_symbol_groups; print('exchange OK')"
python -c "from arbitrage.scanner import discover_triangles; print('scanner OK')"
python -c "from arbitrage.arb import ArbBot; print('arb OK')"
```

- [ ] **Step 2: Verify root backward compat**

```bash
python -c "from config import API_KEY, FEE_RATE; print('config compat OK')"
python -c "from orderbook import OB; print('orderbook compat OK')"
```

- [ ] **Step 3: Verify scripts run (dry-run)**

```bash
python -c "from scripts.run import main; print('scripts/run OK')"
python -c "from scripts.get_token import main; print('scripts/get_token OK')"
python -c "from scripts.find_pair import main; print('scripts/find_pair OK')"
python -c "from scripts.run_dashboard import main; print('scripts/run_dashboard OK')"
```

- [ ] **Step 4: Verify `data/` directory is used**

```bash
ls -la data/
```