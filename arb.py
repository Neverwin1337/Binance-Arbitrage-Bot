import json
import asyncio
import websockets
import config
from orderbook import OB


orderbook = OB()
# 1. 读取 triangles.json
with open('triangles.json', 'r') as f:
    triangles = json.load(f)

# 2. 收集所有symbols，去重
all_symbols = set()
for tri in triangles:
    all_symbols.update([s.lower() for s in tri['symbols']])

all_symbols = list(all_symbols)
group_num = 3
group_size = len(all_symbols) // group_num + (1 if len(all_symbols) % group_num else 0)
groups = [all_symbols[i*group_size:(i+1)*group_size] for i in range(group_num)]

first = True

def get_ab_direction(s1, s2, s3):
    # 統一格式，移除斜杠並轉為大寫
    s1 = s1.replace('/', '').upper()
    s2 = s2.replace('/', '').upper()
    s3 = s3.replace('/', '').upper()
    
    a = s1.replace('USDT', '')
    b = s2.replace('USDT', '')
    
    # 檢查 s1, s2 是否包含 USDT
    if not ('USD' in s1 and 'USD' in s2):
        raise ValueError(f"無效交易對: {s1}, {s2} 必須包含 USDT")
    
    # 檢查 s3 是否為有效交叉對
    if s3 == a + b:
        return True  # A/B（如 BTC/ETH）
    elif s3 == b + a:
        return False  # B/A（如 ETH/BTC）
    else:
        raise ValueError(f"無效交叉交易對: {s3}, 應為 {a+b} 或 {b+a}")
    
async def find_pro(u1,u2,s1):
    uu1 = u1
    uu2 = u2
    ss1 = s1
    u1 = await orderbook.get_ticker(u1)
    u2 = await orderbook.get_ticker(u2)
    s1 = await orderbook.get_ticker(s1)
    if u1 is None or u2 is None or s1 is None:
        return False
    p1 = ((s1["bid"] * u2["bid"]) / u1["ask"])*((1-config.FEE_RATE)**3)
    p2 = ((u1["bid"]) / (u2["ask"]*s1["ask"]))*((1-config.FEE_RATE)**3)
    
    if p1>1:
        print(f"找到利润对:{uu1} -> {ss1} -> {uu2} : {p1}")
    elif p2 >1:
        print(f"找到利润对:{uu2} -> {ss1} -> {uu1} : {p2}")
    else:
        print(p1,p2)


async def listenpair(pair:list):
    while 1:
        try:
            s1 ,s2 , s3 = pair

            
            if "USDT" not in s1:
                if get_ab_direction(s2,s3,s1):
                    await find_pro(s2,s3,s1)
                else:
                    await find_pro(s3,s2,s1)
            elif "USDT" not in s2:
                if get_ab_direction(s1,s3,s2):
                    await find_pro(s1,s3,s2)
                else:
                    await find_pro(s3,s1,s2)
            elif "USDT" not in s3:
                if get_ab_direction(s1,s2,s3):
                    await find_pro(s1,s2,s3)
                else:
                    await find_pro(s2,s1,s3)
            
            await asyncio.sleep(0.2)
        except Exception as e:
            print(e)
            break

async def handle_depth_message(msg):
    global first
    if first:
        print(msg)
        first = False
    data = json.loads(msg)
    if "data" in data:  # 合并流格式
        symbol = data["stream"].replace("@depth5@100ms","").upper()
        stream_data = data["data"]
        bids = stream_data["bids"]
        asks = stream_data["asks"]
        await orderbook.update_orderbook(symbol, bids, asks)



async def listen_ws(symbols):
    streams = [f"{symbol}@depth5@100ms" for symbol in symbols]
    url = f"wss://stream.binance.com:9443/stream?streams={'/'.join(streams)}"
    async with websockets.connect(url) as ws:
        async for msg in ws:
            asyncio.create_task(handle_depth_message(msg))

async def periodic_save_orderbook(interval=2):
    while True:
        json.dump(orderbook.orderbooks, open("ob.json", "w"))
        await asyncio.sleep(interval)

async def main():
    tasks = [listen_ws(group) for group in groups]
    tasks.append(periodic_save_orderbook())
    tasks.extend(listenpair(tri["symbols"]) for tri in triangles)

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())


