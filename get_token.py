from binance.client import Client
import config
import json
import requests
import time
from itertools import combinations
client = Client(config.API_KEY, config.API_SECRET)

# 获取所有现货交易对信息
exchange_info = client.get_exchange_info()
symbols = exchange_info['symbols']

# 只保留现货（SPOT）交易对
spot_symbols = [s['symbol'] for s in symbols if s['status'] == 'TRADING' and s['isSpotTradingAllowed']]

usdt = []
usdc = []
bnb = []
btc = []
eth = []
for i in spot_symbols:

        if i[-4:] == "USDT":
            usdt.append(i)
        elif i[-4:] == "USDC":
            usdc.append(i)
        elif i[-3:] == "BNB":
            bnb.append(i)
        elif i[-3:] == "BTC":
            btc.append(i)
        elif i[-3:] == "ETH":
            eth.append(i)

json.dump({
    "usdt":usdt,
    "usdc":usdc,
    "bnb":bnb,
    "btc":btc,
    "eth":eth,
},open("token.json",'w'))
