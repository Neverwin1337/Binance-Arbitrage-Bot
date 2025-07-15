import asyncio
class OB:
    orderbooks = {}
    l = asyncio.Lock()
    
    async def update_orderbook(self, symbol, bids, asks):
        # bids, asks: [["price", "qty"], ...]
        async with self.l:
            best_bid = float(bids[0][0]) if bids else None
            best_bid_amount = float(bids[0][1]) if bids else None
            best_ask = float(asks[0][0]) if asks else None
            best_ask_amount = float(asks[0][1]) if asks else None
            self.orderbooks[symbol] = {"bid": best_bid, "bid_amount": best_bid_amount, "ask": best_ask, "ask_amount": best_ask_amount}

    async def get_ticker(self,symbol):
        try:
            return self.orderbooks[symbol]
        except:
            return None