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