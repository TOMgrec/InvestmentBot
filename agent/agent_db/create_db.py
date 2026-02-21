from agent.agent_db.utils import create_tables, get_db_overview, check_schema, insert_stock_with_tags, reset_base
from agent.core.config import POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
import json

import pandas as pd

SP500_DATA = "database/sp500-companies.csv"

def assign_tags_simple(row):
    industry = row['Industry']
    sub_industry = row['Sub-Industry']

    # Dictionnaire de correspondance Industry -> Tag
    industry_to_tag = {
        "Health Care": "SANTE",
        "Industrials": "INDUS",
        "Information Technology": "TECH",
        "Financials": "FIN",
        "Consumer Staples": "CONSO",
        "Consumer Discretionary": "CONSO",
        "Energy": "ENERG",
        "Utilities": "UTIL",
        "Real Estate": "IMMO",
        "Materials": "MAT",
        "Communication Services": "COM",
    }

    # Dictionnaire de correspondance Sub-Industry -> Tag
    sub_industry_to_tag = {
        "Pharmaceuticals": "SANTE",
        "Biotechnology": "SANTE",
        "Software": "TECH",
        "IT Services": "TECH",
        "Banks": "FIN",
        "Insurance": "FIN",
        "Automobiles": "AUTO",
        "Retailing": "RETAIL",
        "Oil & Gas": "ENERG",
        "Aerospace & Defense": "AERO",
        "Industrial Conglomerates": "DIV",
        "Luxury Goods": "LUXE",
        "Cloud Computing": "CLOUD",
        "Semiconductors": "TECH",
        "Telecommunication Services": "TELECOM",
    }

    tags = set()

    # Ajouter le tag basé sur l'Industry
    if industry in industry_to_tag:
        tags.add(industry_to_tag[industry])

    # Ajouter le tag basé sur la Sub-Industry
    if sub_industry in sub_industry_to_tag:
        tags.add(sub_industry_to_tag[sub_industry])

    # Retourner les tags sous forme de chaîne séparée par des virgules
    return list(tags)



def create_db():
    """Create the database tables according to the schema."""
    reset_base()  # Optionnel : réinitialise la base avant de créer les tables
    create_tables()
    print("Database tables created successfully.")

    f=pd.read_csv(SP500_DATA)
    for _, row in f.iterrows():
        insert_stock_with_tags(
            stock_data=(
                row['Ticker'], 
                row['Name'], 
                row['Industry'], 
                3,  # rating
                row['description']   # description
            ),
            tags=assign_tags_simple(row)
        )

    overview = get_db_overview(POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
    print(json.dumps(overview, indent=2, default=str))


if __name__ == "__main__":
    create_db()
