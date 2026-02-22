"""
Utilitaires pour récupérer les données financières via yfinance
"""
import yfinance as yf
import pandas as pd
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_tickers_from_sql_result(sql_result: Any, ticker_column: str = "ticker") -> List[str]:
    """
    Extrait les tickers d'un résultat de requête SQL.
    
    Args:
        sql_result: Résultat de requête SQL (peut être JSON, dict, DataFrame, ou liste)
        ticker_column: Nom de la colonne contenant les tickers
        
    Returns:
        Liste des tickers uniques
    """
    tickers = []
    
    # Si c'est un DataFrame pandas
    if isinstance(sql_result, pd.DataFrame):
        if ticker_column in sql_result.columns:
            tickers = sql_result[ticker_column].unique().tolist()
        else:
            raise ValueError(f"Colonne '{ticker_column}' non trouvée. Colonnes disponibles: {list(sql_result.columns)}")
    
    # Si c'est un dictionnaire
    elif isinstance(sql_result, dict):
        if ticker_column in sql_result:
            tickers = sql_result[ticker_column]
            if not isinstance(tickers, list):
                tickers = [tickers]
        else:
            raise ValueError(f"Clé '{ticker_column}' non trouvée dans le dictionnaire")
    
    # Si c'est un JSON (string)
    elif isinstance(sql_result, str):
        import json
        try:
            data = json.loads(sql_result)
            return extract_tickers_from_sql_result(data, ticker_column)
        except json.JSONDecodeError:
            raise ValueError("Impossible de parser le JSON")
    
    # Si c'est une liste
    elif isinstance(sql_result, list):
        for item in sql_result:
            if isinstance(item, dict):
                if ticker_column in item:
                    ticker = item[ticker_column]
                    if ticker not in tickers:
                        tickers.append(ticker)
            else:
                tickers.append(item)
    
    # Nettoyer et valider les tickers
    tickers = [str(t).strip().upper() for t in tickers if t]
    return list(set(tickers))  # Retourner les tickers uniques


def fetch_ticker_data(
    tickers: List[str],
    period: str = "1y",
    interval: str = "1d",
    progress: bool = False
) -> Dict[str, pd.DataFrame]:
    """
    Récupère les données de prix pour une liste de tickers.
    
    Args:
        tickers: Liste des tickers
        period: Période ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'max')
        interval: Intervalle ('1m', '5m', '15m', '30m', '60m', '1d', '1wk', '1mo')
        progress: Afficher la barre de progression
        
    Returns:
        Dictionnaire {ticker: DataFrame avec les données OHLCV}
    """
    logger.info(f"Récupération des données pour {len(tickers)} ticker(s): {', '.join(tickers)}")
    
    result = {}
    failed_tickers = []
    
    for ticker in tickers:
        try:
            logger.info(f"Récupération des données pour {ticker}...")
            data = yf.download(
                ticker,
                period=period,
                interval=interval,
                progress=progress,
                threads=True
            )
            
            if data.empty:
                logger.warning(f"Aucune donnée trouvée pour {ticker}")
                failed_tickers.append(ticker)
            else:
                result[ticker] = data
                logger.info(f"✓ {ticker}: {len(data)} lignes récupérées")
                
        except Exception as e:
            logger.error(f"✗ Erreur lors de la récupération pour {ticker}: {str(e)}")
            failed_tickers.append(ticker)
    
    if failed_tickers:
        logger.warning(f"Tickers non trouvés ou avec erreurs: {', '.join(failed_tickers)}")
    
    return result


def get_ticker_info(tickers: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Récupère les informations générales sur les tickers.
    
    Args:
        tickers: Liste des tickers
        
    Returns:
        Dictionnaire {ticker: {clé_info: valeur}}
    """
    logger.info(f"Récupération des infos pour {len(tickers)} ticker(s)")
    
    result = {}
    
    for ticker in tickers:
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            
            # Extraire les infos pertinentes
            relevant_info = {
                "name": info.get("longName", "N/A"),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "market_cap": info.get("marketCap", "N/A"),
                "pe_ratio": info.get("trailingPE", "N/A"),
                "dividend_yield": info.get("dividendYield", "N/A"),
                "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
                "52_week_low": info.get("fiftyTwoWeekLow", "N/A"),
                "50_day_average": info.get("fiftyDayAverage", "N/A"),
                "200_day_average": info.get("twoHundredDayAverage", "N/A"),
                "current_price": info.get("currentPrice", "N/A"),
            }
            
            result[ticker] = relevant_info
            logger.info(f"✓ Infos récupérées pour {ticker}")
            
        except Exception as e:
            logger.error(f"✗ Erreur lors de la récupération d'infos pour {ticker}: {str(e)}")
            result[ticker] = {"error": str(e)}
    
    return result


def get_latest_price(tickers: List[str]) -> Dict[str, float]:
    """
    Récupère le dernier prix de clôture pour chaque ticker.
    
    Args:
        tickers: Liste des tickers
        
    Returns:
        Dictionnaire {ticker: prix}
    """
    logger.info(f"Récupération des derniers prix pour {len(tickers)} ticker(s)")
    
    result = {}
    
    for ticker in tickers:
        try:
            ticker_obj = yf.Ticker(ticker)
            price = ticker_obj.info.get("currentPrice") or ticker_obj.history(period="1d")["Close"].iloc[-1]
            result[ticker] = price
            logger.info(f"✓ {ticker}: ${price:.2f}" if isinstance(price, (int, float)) else f"✓ {ticker}")
            
        except Exception as e:
            logger.error(f"✗ Erreur pour {ticker}: {str(e)}")
            result[ticker] = None
    
    return result


def process_sql_result_with_yfinance(
    sql_result: Any,
    ticker_column: str = "ticker",
    data_type: str = "price",  # 'price', 'info', 'historical'
    **kwargs
) -> Dict[str, Any]:
    """
    Pipeline complet : extrait les tickers et récupère les données yfinance.
    
    Args:
        sql_result: Résultat de la requête SQL
        ticker_column: Colonne contenant les tickers
        data_type: Type de données à récupérer ('price', 'info', 'historical')
        **kwargs: Arguments additionnels (period, interval, etc.)
        
    Returns:
        Dictionnaire avec résultats et métadonnées
    """
    try:
        # Extraire les tickers
        tickers = extract_tickers_from_sql_result(sql_result, ticker_column)
        logger.info(f"Tickers extraits: {tickers}")
        
        # Récupérer les données selon le type demandé
        if data_type == "price":
            data = get_latest_price(tickers)
        elif data_type == "info":
            data = get_ticker_info(tickers)
        elif data_type == "historical":
            period = kwargs.get("period", "1y")
            interval = kwargs.get("interval", "1d")
            data = fetch_ticker_data(tickers, period=period, interval=interval)
        else:
            raise ValueError(f"data_type '{data_type}' non supporté")
        
        return {
            "status": "success",
            "tickers_count": len(tickers),
            "tickers": tickers,
            "data_type": data_type,
            "data": data
        }
        
    except Exception as e:
        logger.error(f"Erreur dans process_sql_result_with_yfinance: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }
