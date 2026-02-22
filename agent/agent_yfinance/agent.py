"""
Agent YFinance - Récupère les données financières pour les tickers présents dans une requête SQL
"""
from fastapi import FastAPI
from langserve import add_routes
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
import json
import logging

from agent.agent_yfinance.utils import (
    process_sql_result_with_yfinance,
    extract_tickers_from_sql_result,
    get_latest_price,
    get_ticker_info,
    fetch_ticker_data
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Modèles Pydantic pour les entrées/sorties
class YFinanceInput(BaseModel):
    """
    Entrée pour l'agent YFinance.
    Accepte un résultat de requête SQL et récupère les données yfinance pour les tickers.
    """
    sql_result: Any = Field(
        ...,
        description="Résultat de la requête SQL (JSON, DataFrame, dict List, etc.)"
    )
    ticker_column: str = Field(
        default="ticker",
        description="Nom de la colonne contenant les tickers"
    )
    data_type: str = Field(
        default="price",
        description="Type de données à récupérer: 'price' (dernier prix), 'info' (infos générales), 'historical' (historique)"
    )
    period: str = Field(
        default="1y",
        description="Période pour les données historiques (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max)"
    )
    interval: str = Field(
        default="1d",
        description="Intervalle pour les données historiques (1m, 5m, 15m, 30m, 60m, 1d, 1wk, 1mo)"
    )


class YFinanceOutput(BaseModel):
    """Sortie de l'agent YFinance"""
    status: str = Field(description="Status de l'exécution (success ou error)")
    tickers_count: Optional[int] = Field(description="Nombre de tickers trouvés")
    tickers: Optional[List[str]] = Field(description="Liste des tickers")
    data_type: Optional[str] = Field(description="Type de données récupérées")
    data: Optional[Dict[str, Any]] = Field(description="Données récupérées")
    error: Optional[str] = Field(description="Message d'erreur si applicable")


def handle_yfinance_request(llm_input: YFinanceInput) -> YFinanceOutput:
    """
    Traite une requête YFinance.
    
    Args:
        llm_input: Entrée structurée avec le résultat SQL et les paramètres
        
    Returns:
        Résultat avec les données yfinance
    """
    logger.info(f"Traitement request YFinance - Colonne ticker: {llm_input.ticker_column}, "
                f"Type données: {llm_input.data_type}")
    
    # Si la requête SQL est une string JSON, la parser
    sql_result = llm_input.sql_result
    if isinstance(sql_result, str):
        try:
            sql_result = json.loads(sql_result)
            logger.info("Résultat JSON parsé")
        except json.JSONDecodeError:
            logger.warning("Impossible de parser le résultat comme JSON, traiter comme string")
    
    # Appeler le pipeline yfinance
    result = process_sql_result_with_yfinance(
        sql_result=sql_result,
        ticker_column=llm_input.ticker_column,
        data_type=llm_input.data_type,
        period=llm_input.period,
        interval=llm_input.interval
    )
    
    # Convertir les résultats pour la sortie
    output_data = {}
    if result.get("status") == "success":
        data = result.get("data", {})
        
        # Convertir les DataFrames en JSON si nécessaire
        if llm_input.data_type == "historical":
            for ticker, df in data.items():
                # Garder seulement les 10 dernières lignes avec les colonnes essentielles
                output_data[ticker] = {
                    "last_10_days": df[["Open", "High", "Low", "Close", "Volume"]].tail(10).to_dict("records"),
                    "summary": {
                        "total_records": len(df),
                        "start_date": str(df.index[0]),
                        "end_date": str(df.index[-1])
                    }
                }
        else:
            output_data = data
    
    return YFinanceOutput(
        status=result.get("status"),
        tickers_count=result.get("tickers_count"),
        tickers=result.get("tickers"),
        data_type=result.get("data_type"),
        data=output_data,
        error=result.get("error")
    )


# Configuration FastAPI avec LangServe
app = FastAPI(
    title="YFinance Agent",
    description="Agent qui récupère les données financières pour les tickers d'une requête SQL"
)

# Créer une chaîne simple qui traite l'entrée
yfinance_chain = lambda x: handle_yfinance_request(x)

# Exposer le chaîne via LangServe
add_routes(
    app,
    yfinance_chain,
    input_type=YFinanceInput,
    output_type=YFinanceOutput,
    path="/yfinance"
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
