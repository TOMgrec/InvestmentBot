import os
from dotenv import load_dotenv

# Charger les variables d'environnement à partir du fichier .env
load_dotenv()

# --- Clés d'API ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEC_API_KEY = os.getenv("SEC_API_KEY")
FMP_API_KEY = os.getenv("FMP_API_KEY")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")
MARKETAUX_KEY = os.getenv("MARKETAUX_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

# --- Configuration de la base de données PostgreSQL ---
DATABASE_URL = os.getenv("DATABASE_URL")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")

