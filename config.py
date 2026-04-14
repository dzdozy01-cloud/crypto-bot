import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
CHECK_INTERVAL = 60
