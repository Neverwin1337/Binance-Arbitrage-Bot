import asyncio
from typing import TypedDict, Optional


class TickerData(TypedDict):
    bid: Optional[float]
    bid_amount: Optional[float]
    ask: Optional[float]
    ask_amount: Optional[float]


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
