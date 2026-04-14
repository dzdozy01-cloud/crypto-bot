import requests

BASE_URL = "https://api.coingecko.com/api/v3"

COIN_IDS = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "bnb": "binancecoin",
    "sol": "solana",
    "xrp": "ripple",
    "ada": "cardano",
    "doge": "dogecoin",
    "usdt": "tether",
    "ton": "the-open-network",
    "dot": "polkadot",
}

def get_price(coin_symbol):
    symbol = coin_symbol.lower()
    coin_id = COIN_IDS.get(symbol, symbol)
    try:
        response = requests.get(
            f"{BASE_URL}/simple/price",
            params={
                "ids": coin_id,
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_24hr_vol": "true",
                "include_market_cap": "true",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        if coin_id not in data:
            return None
        coin_data = data[coin_id]
        return {
            "symbol": symbol.upper(),
            "price": coin_data.get("usd", 0),
            "change_24h": coin_data.get("usd_24h_change", 0),
            "volume_24h": coin_data.get("usd_24h_vol", 0),
            "market_cap": coin_data.get("usd_market_cap", 0),
        }
    except Exception as e:
        print(f"API Error: {e}")
        return None

def get_multiple_prices(symbols):
    coin_ids = []
    symbol_map = {}
    for symbol in symbols:
        s = symbol.lower()
        coin_id = COIN_IDS.get(s, s)
        coin_ids.append(coin_id)
        symbol_map[coin_id] = s.upper()
    try:
        response = requests.get(
            f"{BASE_URL}/simple/price",
            params={
                "ids": ",".join(coin_ids),
                "vs_currencies": "usd",
                "include_24hr_change": "true",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        results = []
        for coin_id, symbol in symbol_map.items():
            if coin_id in data:
                results.append({
                    "symbol": symbol,
                    "price": data[coin_id].get("usd", 0),
                    "change_24h": data[coin_id].get("usd_24h_change", 0),
                })
        return results
    except Exception as e:
        print(f"API Error: {e}")
        return []

def format_price(coin_data):
    change = coin_data["change_24h"]
    arrow = "UP" if change >= 0 else "DOWN"
    price = coin_data["price"]
    if price >= 1:
        price_str = f"${price:,.2f}"
    else:
        price_str = f"${price:.6f}"
    volume = coin_data.get("volume_24h", 0)
    market_cap = coin_data.get("market_cap", 0)
    return (
        f"{coin_data['symbol']} Price\n"
        f"Price: {price_str}\n"
        f"24h Change: {arrow} {abs(change):.2f}%\n"
        f"Volume: ${volume:,.0f}\n"
        f"Market Cap: ${market_cap:,.0f}"
    )
