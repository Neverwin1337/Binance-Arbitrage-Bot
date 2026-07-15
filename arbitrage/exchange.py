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