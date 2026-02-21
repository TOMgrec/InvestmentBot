# agent/agent_tools/financial_analysis.py

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

import pandas as pd
from financetoolkit import Toolkit  # type: ignore
from langchain.tools import tool


def _init_toolkit_from_statements(
    tickers: List[str],
    balance_sheet: pd.DataFrame,
    income_statement: pd.DataFrame,
    cash_flow: pd.DataFrame,
    reverse_dates: bool = False,
    rounding: int = 4,
) -> Toolkit:
    """
    Helper to initialize FinanceToolkit from pre-normalized financial statements.

    Assumes the data has already been collected and normalized by earlier tools.
    Each DataFrame should be indexed by date (rows) and have standard columns
    expected by FinanceToolkit. [web:2][web:10][web:11]
    """
    toolkit = Toolkit(
        tickers=tickers,
        balance=balance_sheet,
        income=income_statement,
        cash=cash_flow,
        reverse_dates=reverse_dates,
        rounding=rounding,
    )  # [web:2][web:10]
    return toolkit


@tool
def compute_core_financial_ratios(
    balance_sheet_json: Dict[str, Any],
    income_statement_json: Dict[str, Any],
    cash_flow_json: Dict[str, Any],
    tickers: Optional[List[str]] = None,
    ratio_groups: Optional[
        List[Literal["efficiency", "liquidity", "profitability", "solvency", "valuation"]]
    ] = None,
    growth: bool = False,
    trailing_periods: Optional[int] = None,
    rounding: int = 4,
) -> Dict[str, Any]:
    """
    Compute key financial ratios using FinanceToolkit based on structured financial statements.

    Parameters
    ----------
    balance_sheet_json : dict
        Normalized balance sheet data (JSON-serializable) where each key is a ticker
        and the value is a tabular structure convertible to a pandas DataFrame. [web:10][web:11]
    income_statement_json : dict
        Normalized income statement data (same structure as balance_sheet_json).
    cash_flow_json : dict
        Normalized cash flow statement data (same structure as balance_sheet_json).
    tickers : list[str], optional
        Subset of tickers to analyze. If None, all keys in balance_sheet_json are used.
    ratio_groups : list[str], optional
        Which ratio groups to compute: any of
        ["efficiency", "liquidity", "profitability", "solvency", "valuation"].
        If None, all groups are computed. [web:3][web:11]
    growth : bool, default False
        Whether to compute growth of ratios over time when supported. [web:11][web:14]
    trailing_periods : int, optional
        Trailing period (e.g., 4 for TTM with quarterly data) when supported. [web:11]
    rounding : int, default 4
        Number of decimal places to round to. [web:11]

    Returns
    -------
    dict
        JSON-serializable dict with ratio DataFrames converted to nested dicts:
        {
          "efficiency": { ... },
          "liquidity": { ... },
          ...
        }
    """
    # Convert incoming JSON into DataFrames per ticker, then combine.
    # Expect structure: {ticker: {column: {date: value}} or similar tabular form.
    # Upstream tools should normalize this; here we just rely on pandas.DataFrame.
    def _json_to_df_per_ticker(statement_json: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        df_dict: Dict[str, pd.DataFrame] = {}
        for ticker, data in statement_json.items():
            df_dict[ticker] = pd.DataFrame(data)
        return df_dict

    balance_dict = _json_to_df_per_ticker(balance_sheet_json)
    income_dict = _json_to_df_per_ticker(income_statement_json)
    cash_dict = _json_to_df_per_ticker(cash_flow_json)

    if tickers is None:
        tickers = sorted(balance_dict.keys())

    # FinanceToolkit expects combined DataFrames per statement. [web:2][web:7][web:10]
    def _combine_by_ticker(df_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        # Combined multi-index (ticker, date) DataFrame. [web:7]
        combined = pd.concat(df_dict, names=["Ticker"])
        return combined

    balance_combined = _combine_by_ticker({t: balance_dict[t] for t in tickers if t in balance_dict})
    income_combined = _combine_by_ticker({t: income_dict[t] for t in tickers if t in income_dict})
    cash_combined = _combine_by_ticker({t: cash_dict[t] for t in tickers if t in cash_dict})

    toolkit = _init_toolkit_from_statements(
        tickers=tickers,
        balance_sheet=balance_combined,
        income_statement=income_combined,
        cash_flow=cash_combined,
        reverse_dates=False,
        rounding=rounding,
    )

    ratios = toolkit.ratios  # Ratios module of FinanceToolkit. [web:11][web:14]

    if ratio_groups is None:
        ratio_groups = ["efficiency", "liquidity", "profitability", "solvency", "valuation"]

    results: Dict[str, Any] = {}

    def _serialize(df: pd.DataFrame) -> Dict[str, Any]:
        # Convert to JSON-serializable nested dict (index+columns). [web:1][web:11]
        return df.to_dict(orient="index")

    # Efficiency ratios
    if "efficiency" in ratio_groups:
        eff = ratios.collect_efficiency_ratios(
            growth=growth,
            trailing=trailing_periods or 0,
            rounding=rounding,
        )  # [web:11]
        results["efficiency"] = _serialize(eff)

    # Liquidity ratios
    if "liquidity" in ratio_groups:
        liq = ratios.collect_liquidity_ratios(
            growth=growth,
            trailing=trailing_periods or 0,
            rounding=rounding,
        )  # [web:11]
        results["liquidity"] = _serialize(liq)

    # Profitability ratios
    if "profitability" in ratio_groups:
        prof = ratios.collect_profitability_ratios(
            growth=growth,
            trailing=trailing_periods or 0,
            rounding=rounding,
        )  # [web:11]
        results["profitability"] = _serialize(prof)

    # Solvency ratios
    if "solvency" in ratio_groups:
        solv = ratios.collect_solvency_ratios(
            growth=growth,
            trailing=trailing_periods or 0,
            rounding=rounding,
        )  # [web:11]
        results["solvency"] = _serialize(solv)

    # Valuation ratios
    if "valuation" in ratio_groups:
        val = ratios.collect_valuation_ratios(
            growth=growth,
            trailing=trailing_periods or 0,
            rounding=rounding,
        )  # [web:5][web:8][web:11]
        results["valuation"] = _serialize(val)

    return results


@tool
def compute_price_trend_metrics(
    historical_prices_json: Dict[str, Any],
    tickers: Optional[List[str]] = None,
    frequency: Literal["D", "W", "M", "Q", "Y"] = "D",
    window: int = 20,
) -> Dict[str, Any]:
    """
    Compute basic trend metrics (returns, rolling volatility, and moving averages)
    from historical price data for one or more tickers.

    This is a lightweight trend analysis complementing the FinanceToolkit ratios,
    using pandas directly on cleaned price history from data collection tools. [web:7][web:13]

    Parameters
    ----------
    historical_prices_json : dict
        JSON-serializable dict with structure:
        {
          "TICKER": {
            "date": [...],
            "close": [...],
            ...
          },
          ...
        }
        At minimum, a 'close' price series per ticker is required.
    tickers : list[str], optional
        Subset of tickers to analyze. If None, all keys in historical_prices_json are used.
    frequency : {"D", "W", "M", "Q", "Y"}, default "D"
        Resampling frequency for trend analysis (daily, weekly, monthly, etc.).
    window : int, default 20
        Rolling window length for volatility and moving averages.

    Returns
    -------
    dict
        JSON-serializable dict for each ticker with:
        - "returns": percent change series
        - "rolling_volatility": rolling std of returns
        - "sma": simple moving average
        - "ema": exponential moving average
    """
    if tickers is None:
        tickers = sorted(historical_prices_json.keys())

    results: Dict[str, Any] = {}

    for ticker in tickers:
        if ticker not in historical_prices_json:
            continue

        df = pd.DataFrame(historical_prices_json[ticker])
        # Expect a 'date' column or use index; upstream should normalize.
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")

        if "close" not in df.columns:
            # Cannot compute trend metrics without close prices.
            continue

        prices = df["close"].astype(float).sort_index()

        # Optionally resample to requested frequency. [web:7]
        prices = prices.resample(frequency).last()

        returns = prices.pct_change()
        rolling_vol = returns.rolling(window).std()
        sma = prices.rolling(window).mean()
        ema = prices.ewm(span=window, adjust=False).mean()

        # Serialize to JSON-serializable form.
        def _series_to_dict(series: pd.Series) -> Dict[str, float]:
            # Use ISO date string as key.
            return {idx.isoformat(): float(val) for idx, val in series.dropna().items()}

        results[ticker] = {
            "returns": _series_to_dict(returns),
            "rolling_volatility": _series_to_dict(rolling_vol),
            "sma": _series_to_dict(sma),
            "ema": _series_to_dict(ema),
        }

    return results


@tool
def summarize_ratio_trends(
    ratio_data: Dict[str, Any],
    metric_name: str,
    max_points: int = 12,
) -> Dict[str, Any]:
    """
    Create a compact, LLM-friendly summary structure of ratio trends for a specific metric.

    This tool expects the output of compute_core_financial_ratios and extracts a
    single ratio (e.g., 'Return on Equity', 'Current Ratio') over time for each
    ticker, truncated to the most recent `max_points` observations.

    Parameters
    ----------
    ratio_data : dict
        Output of compute_core_financial_ratios (or similar), where each group
        (e.g., 'profitability') contains a nested dict of ratios. [web:1][web:11]
    metric_name : str
        Name of the ratio column to extract from each group DataFrame. The agent
        should pass a specific metric it cares about (e.g., 'Return on Equity').
    max_points : int, default 12
        Maximum number of recent time points to return per ticker.

    Returns
    -------
    dict
        {
          "metric": metric_name,
          "tickers": {
             "AAPL": [
                {"date": "...", "value": ...},
                ...
             ],
             ...
          }
        }

    This structure is designed to be easy for the LLM to interpret when generating
    narrative trend descriptions for reports.
    """
    tickers_summary: Dict[str, List[Dict[str, Union[str, float]]]] = {}

    for group_name, group_data in ratio_data.items():
        # group_data is expected to be a dict index->row from compute_core_financial_ratios.
        df = pd.DataFrame.from_dict(group_data, orient="index")
        if metric_name not in df.columns:
            continue

        # If we have a MultiIndex, assume level 0 is ticker. [web:7]
        if isinstance(df.index, pd.MultiIndex) and "Ticker" in df.index.names:
            for ticker in df.index.get_level_values("Ticker").unique():
                sub_df = df.xs(ticker, level="Ticker").sort_index()
                sub_df = sub_df.tail(max_points)
                series = sub_df[metric_name]

                values = []
                for idx, val in series.items():
                    date_str = idx.isoformat() if hasattr(idx, "isoformat") else str(idx)
                    values.append({"date": date_str, "value": float(val)})

                if values:
                    if ticker not in tickers_summary:
                        tickers_summary[ticker] = []
                    tickers_summary[ticker].extend(values)
        else:
            # Fallback: treat as single-ticker or unknown index; just use index as dates.
            series = df[metric_name].sort_index().tail(max_points)
            values = []
            for idx, val in series.items():
                date_str = idx.isoformat() if hasattr(idx, "isoformat") else str(idx)
                values.append({"date": date_str, "value": float(val)})

            if values:
                tickers_summary.setdefault("UNKNOWN", []).extend(values)

    return {
        "metric": metric_name,
        "tickers": tickers_summary,
    }

