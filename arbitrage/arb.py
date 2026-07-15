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