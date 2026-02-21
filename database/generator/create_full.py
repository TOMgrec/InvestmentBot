import pandas as pd
import financedatabase as fd

# Charger la base de données des equities (actions)
equities = fd.Equities()

# Sélectionner toutes les données (cela inclut les summaries/descriptions)
all_equities = equities.select()

# Lire le fichier CSV
possible_encodings = ['utf-8', 'windows-1252', 'latin1', 'iso-8859-1', 'utf-8-sig', 'cp1252']

for enc in possible_encodings:
    try:
        df = pd.read_csv('database/generator/sp500-companies.csv', encoding=enc)
        print(f"Ça marche avec : {enc}")
        print(df.head())
        break
    except UnicodeDecodeError:
        print(f"Échec avec : {enc}")

# La première colonne est celle des tickers
tickers = df.iloc[:, 0].tolist()  # ou df['ticker_column_name'] si en-tête

# Récupérer les descriptions
descriptions = []
for ticker in tickers:
    try:
        desc = all_equities.loc[ticker.upper()]['summary']  # 'summary' est le champ pour la description
        descriptions.append(desc)
    except KeyError:
        descriptions.append('Description non trouvée')

# Ajouter la nouvelle colonne
df['description'] = descriptions

# Sauvegarder le nouveau fichier CSV
df.to_csv('database/sp500-companies.csv', index=False)

print("Fichier mis à jour sauvegardé sous 'sp500-companies.csv'")