import json
from itertools import combinations

from arbitrage.config import VOLUME_THRESHOLD, DATA_DIR
from arbitrage.exchange import fetch_24hr_volumes
from arbitrage.logger import setup_logger

logger = setup_logger("scanner")


def _get_pair_symbol(a: str, b: str, all_symbols: set[str]) -> str | None:
    if a + b in all_symbols:
        return a + b
    if b + a in all_symbols:
        return b + a
    return None


def discover_triangles() -> list[dict]:
    token_path = f"{DATA_DIR}/token.json"
    with open(token_path, "r") as f:
        data = json.load(f)

    all_symbols: set[str] = set()
    for group in data.values():
        all_symbols.update(group)

    logger.info("Fetching 24hr volumes for %d symbols...", len(all_symbols))
    symbol_volume_map = fetch_24hr_volumes(all_symbols)

    assets: set[str] = set()
    for pair in all_symbols:
        if len(pair) > 6 and pair[-4:] in ("USDT", "USDC"):
            base = pair[:-4]
            quote = pair[-4:]
        else:
            base = pair[:-3]
            quote = pair[-3:]
        assets.add(base)
        assets.add(quote)

    triangles: list[dict] = []
    for a, b, c in combinations(assets, 3):
        ab = _get_pair_symbol(a, b, all_symbols)
        bc = _get_pair_symbol(b, c, all_symbols)
        ca = _get_pair_symbol(c, a, all_symbols)
        if not (ab and bc and ca):
            continue

        usdt_vol_ok = True
        for sym in (ab, bc, ca):
            if "USDT" in sym and symbol_volume_map.get(sym, 0) < VOLUME_THRESHOLD:
                usdt_vol_ok = False
                break
        if usdt_vol_ok:
            triangles.append({
                "route": (a, b, c),
                "symbols": (ab, bc, ca),
            })

    triangles_path = f"{DATA_DIR}/triangles.json"
    with open(triangles_path, "w") as f:
        json.dump(triangles, f)
    logger.info("Found %d triangles, saved to %s", len(triangles), triangles_path)
    return triangles