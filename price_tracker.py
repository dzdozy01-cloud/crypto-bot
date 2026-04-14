import requests
from config import COINGECKO_API_URL

def get_price(coin_id, currency="usd"):
    try:
        url = f"{COINGECKO_API_URL}/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": currency,
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_market_cap": "true"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if coin_id in data:
            return data[coin_id]
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_multiple_prices(coin_ids, currency="usd"):
    try:
        url = f"{COINGECKO_API_URL}/simple/price"
        params = {
            "ids": ",".join(coin_ids),
            "vs_currencies": currency,
            "include_24hr_change": "true",
            "include_market_cap": "true"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return {}

def search_coin(query):
    try:
        url = f"{COINGECKO_API_URL}/search"
        params = {"query": query}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("coins", [])[:5]
    except Exception as e:
        print(f"Error: {e}")
        return []

def get_trending():
    try:
        url = f"{COINGECKO_API_URL}/search/trending"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("coins", [])
    except Exception as e:
        print(f"Error: {e}")
        return []

def get_market_overview(currency="usd", limit=10):
    try:
        url = f"{COINGECKO_API_URL}/coins/markets"
        params = {
            "vs_currency": currency,
            "order": "market_cap_desc",
            "per_page": limit,
            "page": 1,
            "sparkline": False,
            "price_change_percentage": "24h"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return []
