import requests
import json
from itertools import combinations
import time

# 1. 获取所有交易对
with open('token.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

all_symbols = set()
for group in data.values():
    all_symbols.update(group)

# 2. 查询所有symbol的24hr行情，记录volume
url = "https://api.binance.com/api/v3/ticker/24hr"
symbol_volume_map = {}
for symbol in all_symbols:
    resp = requests.get(url, params={'symbol': symbol})
    if resp.status_code == 200:
        t = resp.json()
        symbol_volume_map[symbol] = float(t.get('quoteVolume', 0))
    else:
        symbol_volume_map[symbol] = 0
    time.sleep(0.1)  # 防止限流

# 3. 提取所有币种
assets = set()
for pair in all_symbols:
    if len(pair) > 6:
        base = pair[:-4] if pair[-4:] in ['USDT', 'USDC'] else pair[:-3]
        quote = pair[-4:] if pair[-4:] in ['USDT', 'USDC'] else pair[-3:]
    else:
        base = pair[:-3]
        quote = pair[-3:]
    assets.add(base)
    assets.add(quote)

# 4. 构建币对映射，返回实际symbol名
def get_pair_symbol(a, b):
    if (a + b) in all_symbols:
        return a + b
    elif (b + a) in all_symbols:
        return b + a
    else:
        return None

# 5. 枚举所有三币组合，只要求USDT相关symbol的volume达标
VOLUME_THRESHOLD = 10_000_000  # 你可以调整
triangles = []
for a, b, c in combinations(assets, 3):
    ab = get_pair_symbol(a, b)
    bc = get_pair_symbol(b, c)
    ca = get_pair_symbol(c, a)
    if ab and bc and ca:
        # 只检查三条路径中包含USDT的symbol
        usdt_vol_ok = True
        for sym in (ab, bc, ca):
            if 'USDT' in sym and symbol_volume_map.get(sym, 0) < VOLUME_THRESHOLD:
                usdt_vol_ok = False
                break
        if usdt_vol_ok:
            triangles.append({
                "route": (a, b, c),
                "symbols": (ab, bc, ca)
            })

print(f"过滤后可三角套利币组数量: {len(triangles)}")
json.dump(triangles, open("triangles.json", "w"))
