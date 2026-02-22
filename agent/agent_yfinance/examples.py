"""
Exemples d'utilisation de l'agent YFinance
"""

from agent.agent_yfinance.utils import (
    process_sql_result_with_yfinance,
    extract_tickers_from_sql_result,
    get_latest_price,
    get_ticker_info,
    fetch_ticker_data
)
import pandas as pd
import json


def example_1_simple_price():
    """
    Exemple 1: Récupérer les derniers prix pour une liste simple de tickers
    """
    print("\n" + "="*60)
    print("EXEMPLE 1: Récupérer les derniers prix")
    print("="*60)
    
    # Simuler un résultat SQL simple
    sql_result = {
        "ticker": ["AAPL", "MSFT", "GOOGL"]
    }
    
    result = process_sql_result_with_yfinance(
        sql_result=sql_result,
        ticker_column="ticker",
        data_type="price"
    )
    
    if result["status"] == "success":
        print(f"\n✓ {result['tickers_count']} tickers trouvés")
        for ticker, price in result["data"].items():
            print(f"  {ticker}: ${price:.2f}" if price else f"  {ticker}: N/A")


def example_2_dataframe():
    """
    Exemple 2: Utiliser un DataFrame pandas (comme retourné par une requête SQL)
    """
    print("\n" + "="*60)
    print("EXEMPLE 2: DataFrame avec résultat SQL")
    print("="*60)
    
    # Créer un DataFrame simulant le résultat d'une requête SQL
    df = pd.DataFrame({
        "ticker": ["TSLA", "AMZN", "META"],
        "sector": ["Autos", "Consumer", "Communication"],
        "market_cap": [800000000000, 1700000000000, 500000000000]
    })
    
    result = process_sql_result_with_yfinance(
        sql_result=df,
        ticker_column="ticker",
        data_type="info"
    )
    
    if result["status"] == "success":
        print(f"\n✓ {result['tickers_count']} tickers trouvés: {', '.join(result['tickers'])}")
        print("\nInformations récupérées:")
        for ticker, info in result["data"].items():
            print(f"\n{ticker}:")
            for key, value in info.items():
                if key != "error":
                    print(f"  {key}: {value}")


def example_3_historical():
    """
    Exemple 3: Récupérer l'historique des prix
    """
    print("\n" + "="*60)
    print("EXEMPLE 3: Données historiques")
    print("="*60)
    
    # Résultat SQL en JSON
    sql_result = json.dumps({
        "companies": [
            {"ticker": "NVDA", "name": "NVIDIA"},
            {"ticker": "AMD", "name": "AMD"}
        ]
    })
    
    # Extraire les tickers du JSON
    import json
    data = json.loads(sql_result)
    tickers = [item["ticker"] for item in data["companies"]]
    
    result = get_latest_price(tickers)
    print(f"\n✓ Derniers prix:")
    for ticker, price in result.items():
        if price:
            print(f"  {ticker}: ${price:.2f}")


def example_4_direct_functions():
    """
    Exemple 4: Utiliser les fonctions directement
    """
    print("\n" + "="*60)
    print("EXEMPLE 4: Utilisation directe des fonctions utilitaires")
    print("="*60)
    
    tickers = ["SPY", "QQQ", "IWM"]
    
    print(f"\nRécupération des infos pour: {', '.join(tickers)}")
    info = get_ticker_info(tickers)
    
    for ticker, data in info.items():
        if "error" not in data:
            print(f"\n{ticker}:")
            print(f"  Secteur: {data.get('sector', 'N/A')}")
            print(f"  P/E Ratio: {data.get('pe_ratio', 'N/A')}")
            print(f"  Rendement Dividende: {data.get('dividend_yield', 'N/A')}")


def example_5_list_result():
    """
    Exemple 5: Résultat SQL sous forme de liste
    """
    print("\n" + "="*60)
    print("EXEMPLE 5: Résultat SQL en liste")
    print("="*60)
    
    # Résultat SQL en liste de dictionnaires
    sql_result = [
        {"ticker": "JPM", "company": "JPMorgan Chase"},
        {"ticker": "BAC", "company": "Bank of America"},
        {"ticker": "WFC", "company": "Wells Fargo"}
    ]
    
    result = process_sql_result_with_yfinance(
        sql_result=sql_result,
        ticker_column="ticker",
        data_type="price"
    )
    
    if result["status"] == "success":
        print(f"\n✓ {result['tickers_count']} tickers bancaires trouvés")
        for ticker, price in result["data"].items():
            print(f"  {ticker}: ${price:.2f}" if price else f"  {ticker}: N/A")


if __name__ == "__main__":
    print("\n🚀 Exemples d'utilisation de l'Agent YFinance\n")
    
    # Décommenter les exemples que tu veux exécuter
    example_1_simple_price()
    # example_2_dataframe()
    # example_3_historical()
    # example_4_direct_functions()
    # example_5_list_result()
    
    print("\n" + "="*60)
    print("Exemples terminés!")
    print("="*60 + "\n")
