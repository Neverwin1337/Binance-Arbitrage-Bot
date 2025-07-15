# 币安套利机器人 / Binance Arbitrage Bot

## 项目简介 / Project Introduction

本项目是一个基于Python的币安现货稳定币三角套利机器人，支持自动发现套利机会、模拟和实盘操作，并可动态筛选高流动性币对。

This project is a Python-based Binance spot stablecoin triangular arbitrage bot. It can automatically discover arbitrage opportunities, supports both simulation and live trading, and dynamically filters high-liquidity pairs.

---

## 主要功能 / Main Features
- 自动获取币安现货所有交易对
- 动态筛选高流动性币种和交易对
- 自动寻找三角套利路径（如 USDT → u1 → u2 → USDT）
- 支持模拟和实盘套利
- 订单簿实时监控与套利决策
- 详细日志与结果输出

- Automatically fetches all Binance spot trading pairs
- Dynamically filters high-liquidity tokens and pairs
- Automatically finds triangular arbitrage paths (e.g., USDT → u1 → u2 → USDT)
- Supports both simulation and live arbitrage
- Real-time orderbook monitoring and arbitrage decision-making
- Detailed logging and result output

---

## 使用方法 / Usage



### 2. 配置API密钥 / Configure API Keys
在 `config.py` 文件中填写你的币安 API_KEY 和 API_SECRET。

Fill in your Binance `API_KEY` and `API_SECRET` in the `config.py` file.

### 3. 运行主程序 / Run Main Script
```bash
python arb.py
```

你也可以运行其它辅助脚本，如 `get_token.py`、`find_pair.py` 等。
You can also run other helper scripts such as `get_token.py`, `find_pair.py`, etc.

---

## 文件说明 / File Description
- `arb.py`：主套利逻辑脚本 / Main arbitrage logic script
- `orderbook.py`：订单簿数据获取与处理 / Orderbook data fetch & processing
- `orderbook_dashboard.py`：订单簿可视化 / Orderbook dashboard visualization
- `get_token.py`：获取并筛选币安交易对 / Fetch and filter Binance pairs
- `find_pair.py`：三角套利路径查找 / Triangular arbitrage path finder
- `token.json`：币安现货所有交易对数据 / All Binance spot pairs data
- `triangles.json`：三角套利路径数据 / Triangular arbitrage paths data
- `ob.json`：订单簿快照数据 / Orderbook snapshot data
- `config.py`：API密钥配置 / API key configuration

---

## 免责声明 / Disclaimer

本项目仅供学习与研究使用，任何因使用本项目代码进行实盘交易造成的损失，作者不承担任何责任。

This project is for educational and research purposes only. The author is not responsible for any losses incurred from using this code for live trading. 