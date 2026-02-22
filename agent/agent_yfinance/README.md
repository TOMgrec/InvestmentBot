# Agent YFinance 📊

Agent qui récupère les données financières via **yfinance** pour les tickers présents dans un résultat de requête SQL.

## Fonctionnalités

- ✅ **Extraction automatique de tickers** depuis différents formats (JSON, DataFrame pandas, dict, liste)
- ✅ **Récupération de derniers prix** en temps réel
- ✅ **Infos détaillées** sur les entreprises (secteur, P/E ratio, capitalisation, etc.)
- ✅ **Données historiques** OHLCV (Open, High, Low, Close, Volume)
- ✅ **Gestion d'erreurs** avec logging détaillé
- ✅ **API REST** via FastAPI/LangServe

## Installation

Les dépendances sont dans `requirements.txt`. Installe-les avec :

```bash
pip install -r requirements.txt
```

yfinance a été défini comme dépendance obligatoire.

## Utilisation

### 1. En tant que module Python

```python
from agent.agent_yfinance.utils import process_sql_result_with_yfinance

# Résultat d'une requête SQL (peut être JSON, DataFrame, dict, etc.)
sql_result = {
    "ticker": ["AAPL", "MSFT", "GOOGL"]
}

# Récupérer les derniers prix
result = process_sql_result_with_yfinance(
    sql_result=sql_result,
    ticker_column="ticker",
    data_type="price"  # ou "info" ou "historical"
)

if result["status"] == "success":
    print(result["data"])
```

### 2. Via l'API REST

Démarrer le serveur :
```bash
python agent/agent_yfinance/agent.py
```

Serveur disponible sur `http://localhost:8002`

Exemple via curl :
```bash
curl -X POST "http://localhost:8002/yfinance/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "sql_result": {"ticker": ["AAPL", "MSFT"]},
    "ticker_column": "ticker",
    "data_type": "price"
  }'
```

### 3. Avec des DataFrames pandas

```python
import pandas as pd
from agent.agent_yfinance.utils import process_sql_result_with_yfinance

# DataFrame retourné par une requête SQL
df = pd.DataFrame({
    "ticker": ["TSLA", "AMZN"],
    "sector": ["Autos", "Consumer"]
})

result = process_sql_result_with_yfinance(
    sql_result=df,
    ticker_column="ticker",
    data_type="info"
)
```

## Types de données supportés

### `data_type="price"` (Défaut)
Retourne le dernier prix de clôture pour chaque ticker.
```python
{
    "AAPL": 150.25,
    "MSFT": 380.42,
    "GOOGL": 140.18
}
```

### `data_type="info"`
Retourne des informations détaillées sur chaque ticker.
```python
{
    "AAPL": {
        "name": "Apple Inc.",
        "sector": "Technology",
        "market_cap": 2800000000000,
        "pe_ratio": 28.5,
        "dividend_yield": 0.0045,
        ...
    }
}
```

### `data_type="historical"`
Retourne l'historique des prix OHLCV.
```python
{
    "AAPL": {
        "last_10_days": [
            {"Open": 150.1, "High": 151.5, "Low": 150.0, "Close": 151.2, "Volume": 50000000},
            ...
        ],
        "summary": {
            "total_records": 252,
            "start_date": "2024-01-01",
            "end_date": "2025-01-01"
        }
    }
}
```

## Formats de résultat SQL supportés

### JSON (string)
```python
sql_result = '{"ticker": ["AAPL", "MSFT"]}'
```

### Dictionnaire
```python
sql_result = {"ticker": ["AAPL", "MSFT"]}
```

### DataFrame pandas
```python
sql_result = pd.DataFrame({"ticker": ["AAPL", "MSFT"]})
```

### Liste de dictionnaires
```python
sql_result = [
    {"ticker": "AAPL", "company": "Apple"},
    {"ticker": "MSFT", "company": "Microsoft"}
]
```

## Paramètres

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| `sql_result` | - | Résultat de la requête SQL |
| `ticker_column` | `"ticker"` | Nom de la colonne contenant les tickers |
| `data_type` | `"price"` | Type de données: `price`, `info`, `historical` |
| `period` | `"1y"` | Période pour l'historique: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max |
| `interval` | `"1d"` | Intervalle pour l'historique: 1m, 5m, 15m, 30m, 60m, 1d, 1wk, 1mo |

## Exemples complets

Voir [examples.py](examples.py) pour des exemples d'utilisation complète.

```bash
python agent/agent_yfinance/examples.py
```

## Architecture

```
agent_yfinance/
├── __init__.py          # Package init
├── agent.py             # FastAPI app et endpoints
├── utils.py             # Fonctions utilitaires yfinance
├── examples.py          # Exemples d'utilisation
└── README.md            # Cette documentation
```

### Fonctions principales dans `utils.py`

- `extract_tickers_from_sql_result()` - Extrait les tickers du résultat SQL
- `fetch_ticker_data()` - Récupère l'historique des prix
- `get_ticker_info()` - Récupère les infos détaillées
- `get_latest_price()` - Récupère les derniers prix
- `process_sql_result_with_yfinance()` - Pipeline complet

## Logging

L'agent enregistre toutes les opérations. Pour augmenter le niveau de verbosité :

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Gestion d'erreurs

L'agent gère gracieusement les erreurs :
- Tickers invalides ou introuvables
- Problèmes de connexion API
- Données manquantes

Chaque réponse inclut un champ `status` (success/error) et des messages d'erreur détaillés en cas de problème.

## Limitations

- yfinance dépend de sources de données externes (peut avoir des délais)
- Les données sont fetched en temps réel (peut être lent pour beaucoup de tickers)
- Certains tickers peuvent ne pas avoir toutes les infos disponibles

## Intégration avec l'agent SQL

Workflow type:
1. **Agent SQL** (agent_db) exécute une requête et retourne une liste de tickers
2. **Agent YFinance** prend ce résultat en entrée
3. Récupère les données financières pour chaque ticker
4. Retourne les données structurées

```python
# Exemple d'intégration
from agent.agent_db.utils import send_query
from agent.agent_yfinance.utils import process_sql_result_with_yfinance

# 1. Exécuter une requête SQL pour récupérer les tickers
sql = "SELECT ticker, name FROM companies WHERE sector = 'Technology'"
sql_result = send_query(sql)  # Retourne un DataFrame

# 2. Récupérer les données yfinance
yfinance_result = process_sql_result_with_yfinance(
    sql_result=sql_result,
    ticker_column="ticker",
    data_type="price"
)

print(yfinance_result)
```

## Ports

- **Agent SQL**: Port 8001
- **Agent YFinance**: Port 8002
