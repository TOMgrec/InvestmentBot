#%%
import psycopg2
from psycopg2 import sql
import json, datetime

from agent.core.config import POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD


# Charger le JSON (remplace par ton fichier)
with open("agent/agent_db/schema.json", "r") as f:
    SCHEMA = json.load(f)


def reset_base():
    try:
        connexion = psycopg2.connect(
            host="localhost", port="5432", database=POSTGRES_DB,
            user=POSTGRES_USER, password=POSTGRES_PASSWORD
        )
        cursor = connexion.cursor()
        
        # Supprimer toutes les tables
        cursor.execute("""
            DO $$ 
            DECLARE 
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """)
        
        connexion.commit()
        print("🗑️  Base de données vidée - toutes les tables supprimées")
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
    finally:
        if 'connexion' in locals():
            cursor.close()
            connexion.close()


def insert_stock_with_tags(stock_data, tags):
    """Insère un stock avec ses tags associés dans la base de données."""

    # Connexion à la DB (remplace avec tes credentials)
    conn = psycopg2.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()

    try:
        # Insérer un nouveau stock
        insert_stock = """
            INSERT INTO stocks (code, nom_entreprise, secteur, note, description)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
        """
        cur.execute(insert_stock, stock_data)
        stock_id = cur.fetchone()[0]  # Récupère l'ID auto-généré

        # Insérer des tags (s'ils n'existent pas déjà)
        tag_ids = []
        for tag_nom in tags:
            # Vérifier si le tag existe
            cur.execute("SELECT id FROM tags WHERE nom = %s;", (tag_nom,))
            result = cur.fetchone()
            if result:
                tag_ids.append(result[0])
            else:
                # Insérer si non existant
                cur.execute("INSERT INTO tags (nom) VALUES (%s) RETURNING id;", (tag_nom,))
                tag_ids.append(cur.fetchone()[0])

        # Insérer les associations dans stock_tags
        for tag_id in tag_ids:
            cur.execute("""
                INSERT INTO stock_tags (stock_id, tag_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING;  -- Évite les doublons si déjà associé
            """, (stock_id, tag_id))

        conn.commit()  # Valide la transaction
        print("Insertion réussie !")
    except Exception as e:
        conn.rollback()  # Annule en cas d'erreur
        print(f"Erreur : {e}")
    finally:
        cur.close()
        conn.close()


def create_tables():
    # Connexion (comme ci-dessus)
    conn = psycopg2.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()

    try:
        # Étape 1: Créer les tables dynamiquement
        for table_name, table_info in SCHEMA["tables"].items():
            columns = table_info.get("colonnes", {})  # Note : c'est "colonnes" dans ton JSON
            constraints = table_info.get("contraintes", {})
            
            # Générer la définition des colonnes
            col_defs = []
            for col_name, col_info in columns.items():
                col_type = col_info["type"]
                nullable = "NOT NULL" if not col_info.get("nullable", True) else ""
                pk = "PRIMARY KEY" if col_info.get("primary_key") else ""
                unique = "UNIQUE" if col_info.get("unique") else ""
                default = f"DEFAULT {col_info['default']}" if "default" in col_info else ""
                references = f"REFERENCES {col_info['references']}" if "references" in col_info else ""
                col_def = f"{col_name} {col_type} {nullable} {pk} {unique} {default} {references}".strip()
                col_defs.append(col_def)
            
            # Ajouter la PK composite si présente
            pk_composite = ""
            if "primary_key" in constraints:
                pk_fields = ", ".join(constraints["primary_key"])
                pk_composite = f", PRIMARY KEY ({pk_fields})"
            
            # Requête CREATE
            create_query = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    {", ".join(col_defs)}{pk_composite}
                );
            """
            cur.execute(create_query)
        
        conn.commit()
        print("Tables créées avec succès !")
    
    except Exception as e:
        conn.rollback()
        print(f"Erreur : {e}")
    finally:
        cur.close()
        conn.close()


def check_schema():
    # Connexion (comme ci-dessus)
    conn = psycopg2.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()

    errors = []
    
    # Vérifier existence des tables
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
    existing_tables = [row[0] for row in cur.fetchall()]
    for table in SCHEMA["tables"]:
        if table not in existing_tables:
            errors.append(f"Table {table} manquante.")
    
    # Vérifier colonnes et types pour chaque table
    for table_name, table_info in SCHEMA["tables"].items():
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = %s;
        """, (table_name,))
        db_columns = cur.fetchall()
        db_col_dict = {row[0]: {"type": row[1], "nullable": row[2] == 'YES', "default": row[3]} for row in db_columns}
        
        for col_name, col_info in table_info["colonnes"].items():
            if col_name not in db_col_dict:
                errors.append(f"Colonne {col_name} manquante dans {table_name}.")
                continue
            db_col = db_col_dict[col_name]
            if db_col["type"].lower() != col_info["type"].lower():
                errors.append(f"Type mismatch pour {col_name} dans {table_name}: attendu {col_info['type']}, trouvé {db_col['type']}.")
            if db_col["nullable"] != col_info.get("nullable", True):
                errors.append(f"Nullable mismatch pour {col_name} dans {table_name}.")
            # Vérifier default, PK, etc. (ajoute des requêtes similaires pour constraints si besoin)
    
    # Vérifier contraintes (ex. PK)
    cur.execute("""
        SELECT tc.constraint_name, tc.constraint_type, kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
        WHERE tc.table_name = %s;
    """, (table_name,))
    # Ajoute des checks similaires pour valider vs JSON
    
    if errors:
        raise ValueError("Erreurs de schéma : " + "; ".join(errors))
    print("Schéma validé !")


def get_db_overview():
    """
    Fournit un overview rapide de l'état de la base de données PostgreSQL basée sur le schéma fourni.
    
    :return: Un dictionnaire avec l'overview des tables et stats
    """
    
    overview = {
        'timestamp': datetime.datetime.now().isoformat(),
        'tables': {},
        'stats': {},
        'errors': []
    }
    
    try:
        # Connexion à la DB
        conn = psycopg2.connect(
            dbname=POSTGRES_DB, 
            user=POSTGRES_USER, 
            password=POSTGRES_PASSWORD, 
            host="localhost", 
            port="5432"
        )
        cur = conn.cursor()
        
        # Liste des tables attendues
        expected_tables = list(SCHEMA['tables'].keys())
        
        # Vérifier existence des tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
        """)
        existing_tables = [row[0] for row in cur.fetchall()]
        
        for table in expected_tables:
            if table not in existing_tables:
                overview['errors'].append(f"Table '{table}' manquante.")
        
        # Si erreurs critiques, arrêter
        if overview['errors']:
            return overview
        
        # Overview par table : counts
        for table in expected_tables:
            cur.execute(sql.SQL("SELECT COUNT(*) FROM {};").format(sql.Identifier(table)))
            count = cur.fetchone()[0]
            overview['tables'][table] = {'row_count': count}
        
        # Stats spécifiques pour 'stocks'
        if 'stocks' in expected_tables:
            # Moyenne des notes
            cur.execute("SELECT AVG(note) FROM stocks;")
            avg_note = cur.fetchone()[0]
            overview['stats']['avg_note'] = float(avg_note) if avg_note else None
            
            # Comptage par secteur
            cur.execute("""
                SELECT secteur, COUNT(*) 
                FROM stocks 
                GROUP BY secteur 
                ORDER BY COUNT(*) DESC;
            """)
            sectors = {row[0]: row[1] for row in cur.fetchall()}
            overview['stats']['sectors_distribution'] = sectors
            
            # Stocks récents (derniers 5)
            cur.execute("""
                SELECT code, nom_entreprise, cree_le 
                FROM stocks 
                ORDER BY cree_le DESC 
                LIMIT 5;
            """)
            recent_stocks = [
                {'code': row[0], 'nom_entreprise': row[1], 'cree_le': row[2].isoformat()}
                for row in cur.fetchall()
            ]
            overview['stats']['recent_stocks'] = recent_stocks
        
        # Stats pour 'tags'
        if 'tags' in expected_tables:
            # Tags les plus utilisés (via stock_tags)
            if 'stock_tags' in expected_tables:
                cur.execute("""
                    SELECT t.nom, COUNT(st.stock_id) as usage_count
                    FROM tags t
                    LEFT JOIN stock_tags st ON t.id = st.tag_id
                    GROUP BY t.nom
                    ORDER BY usage_count DESC
                    LIMIT 10;
                """)
                top_tags = {row[0]: row[1] for row in cur.fetchall()}
                overview['stats']['top_tags'] = top_tags
        
        # Stats pour 'stock_tags' (associations)
        if 'stock_tags' in expected_tables:
            # Moyenne de tags par stock
            cur.execute("""
                SELECT AVG(tag_count) 
                FROM (SELECT stock_id, COUNT(tag_id) as tag_count 
                      FROM stock_tags 
                      GROUP BY stock_id) as sub;
            """)
            avg_tags_per_stock = cur.fetchone()[0]
            overview['stats']['avg_tags_per_stock'] = float(avg_tags_per_stock) if avg_tags_per_stock else 0.0
        
    except psycopg2.Error as e:
        overview['errors'].append(f"Erreur PostgreSQL: {e}")
    except Exception as e:
        overview['errors'].append(f"Erreur générale: {e}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()
    
    return overview

def send_query(query):
    """Exécute une requête SQL et retourne les résultats."""
    try:
        conn = psycopg2.connect(
            dbname=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD, host="localhost", port="5432"
        )
        cur = conn.cursor()
        cur.execute(query)
        results = cur.fetchall()
        return results
    except Exception as e:
        print(f"Erreur lors de l'exécution de la requête : {e}")
        return None
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

# %%

if __name__ == "__main__":
    # Exemple d'utilisation
    overview = get_db_overview()
    print(json.dumps(overview, indent=2, default=str))
    req = "SELECT code, nom_entreprise FROM stocks LIMIT 5;"
    results = send_query(req)
    print(results)