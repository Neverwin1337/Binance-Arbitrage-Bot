import os

API_KEY = os.environ.get("BINANCE_API_KEY", "")
API_SECRET = os.environ.get("BINANCE_API_SECRET", "")
FEE_RATE = float(os.environ.get("BINANCE_FEE_RATE", "0.001"))
VOLUME_THRESHOLD = int(os.environ.get("BINANCE_VOLUME_THRESHOLD", "10000000"))
WS_GROUP_COUNT = int(os.environ.get("BINANCE_WS_GROUP_COUNT", "3"))
LOG_LEVEL = os.environ.get("BINANCE_LOG_LEVEL", "INFO")
DATA_DIR = os.environ.get("BINANCE_DATA_DIR", "data")
