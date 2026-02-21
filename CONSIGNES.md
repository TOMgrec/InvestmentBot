# CONSIGNES POUR L'IMPLÉMENTATION DE L'AGENT D'ANALYSE FINANCIÈRE

## MISSION

Tu es un agent expert en développement logiciel. Ta mission est de construire une application d'analyse financière basée sur des agents IA, en suivant scrupuleusement les instructions ci-dessous. Tu dois implémenter la structure de projet, la stack technique et les modules dans l'ordre séquentiel défini.

---

## 1. Structure des Fichiers et Dossiers

Tu dois d'abord créer la structure de projet suivante. Chaque fichier et dossier a un rôle précis.

```
/
├── agent/                          # Cœur du backend de l'agent
│   ├── __init__.py
│   ├── agent_db/                   # Module pour l'interaction avec les bases de données
│   │   ├── __init__.py
│   │   ├── database.py             # Logique de connexion (SQLAlchemy, PyMongo, Redis)
│   │   ├── models.py               # Modèles de tables PostgreSQL (SQLAlchemy)
│   │   └── crud.py                 # Fonctions de base (Create, Read, Update)
│   ├── agent_langgraph/            # Logique de l'agent avec LangGraph
│   │   ├── __init__.py
│   │   ├── graph.py                # Définition du graphe LangGraph (nœuds, arêtes)
│   │   ├── nodes.py                # Implémentation de la logique de chaque nœud
│   │   └── state.py                # Définition de l'état de l'agent (AgentState)
│   ├── agent_tools/                # Outils (Tools) pour LangChain/LangGraph
│   │   ├── __init__.py
│   │   ├── data_collection.py      # Outils pour la collecte de données externes
│   │   └── financial_analysis.py   # Outils pour l'analyse financière (ratios, etc.)
│   ├── core/                       # Configuration et logique de base
│   │   ├── __init__.py
│   │   └── config.py               # Chargement des variables d'environnement
│   ├── api/                        # API FastAPI
│   │   ├── __init__.py
│   │   ├── routers.py              # Endpoints de l'API (ex: /agent/query)
│   │   └── schemas.py              # Schémas Pydantic pour la validation des données
│   └── main.py                     # Point d'entrée de l'application FastAPI
│
├── app/                            # Application Frontend avec Chainlit
│   └── app.py                      # Logique de l'interface utilisateur
│
├── tests/                          # Tests unitaires et d'intégration
│   ├── __init__.py
│   ├── test_api.py
│   └── test_tools.py
│
├── scripts/                        # Scripts utiles
│   └── seed_db.py                  # Script pour peupler la base de données initiale
│
├── docker-compose.yml              # Orchestration des conteneurs
├── Dockerfile                      # Pour construire l'image de l'agent backend
├── .env                            # Fichier pour les secrets (ignoré par git)
├── .env.example                    # Modèle pour le fichier .env
├── .gitignore
├── pyproject.toml                  # Fichier de projet et dépendances (Poetry)
└── README.md                       # Documentation du projet
```

---

## 2. Stack Technique et Configuration

### Stack Technique à Utiliser
- **Backend**: Python 3.11+, FastAPI
- **Bases de données**: PostgreSQL + pgvector, MongoDB, Redis (pour le caching)
- **Framework Agent**: LangChain, LangGraph
- **LLM**: OpenAI (GPT-4o-mini, text-embedding-3-small)
- **Frontend**: Chainlit
- **Dépendances**: Poetry
- **Qualité de code**: `black` pour le formatage, `ruff` pour le linting
- **Orchestration**: Docker, Docker Compose

### Configuration Initiale
1.  **Poetry**: Initialise le projet avec `poetry init` et gère toutes les dépendances via `pyproject.toml`.
2.  **Variables d'Environnement**: Crée un fichier `.env.example` avec toutes les clés nécessaires (API Keys, DB credentials). Le fichier `.env` sera utilisé en local et ignoré par git.
    ```.env.example
    # OpenAI
    OPENAI_API_KEY="sk-..."

    # Database
    POSTGRES_USER="user"
    POSTGRES_PASSWORD="password"
    POSTGRES_DB="finance"
    DATABASE_URL="postgresql+psycopg2://user:password@postgres/finance"

    MONGO_INITDB_ROOT_USERNAME="mongo"
    MONGO_INITDB_ROOT_PASSWORD="password"
    MONGO_URL="mongodb://mongo:password@mongo:27017/"

    # Redis
    REDIS_URL="redis://redis:6379"

    # External APIs
    SEC_API_KEY=""
    FMP_API_KEY=""
    NEWSAPI_KEY=""
    ALPHA_VANTAGE_KEY=""
    MARKETAUX_KEY=""
    FINNHUB_API_KEY=""
    ```
3.  **Qualité de Code**: Configure `pyproject.toml` pour utiliser `black` et `ruff` afin d'assurer un code propre et cohérent.

---

## 3. Plan d'Implémentation Séquentiel

Tu dois suivre ce plan étape par étape. Ne passe pas à un module sans avoir validé le précédent.

### Module 1: Base de Données, API et Agent (LangGraph)

**Objectif**: Créer le squelette fonctionnel de l'application avec les bases de données, une API de base et un agent LangGraph capable de gérer un flux simple.

1.  **`docker-compose.yml`**:
    - Définis les services: `postgres` (avec `pgvector/pgvector:pg16`), `mongo` (`mongo:7`), `redis` (`redis:latest`), et `agent` (build depuis le `Dockerfile`).
    - Lie les volumes pour la persistance des données de Postgres et Mongo.
    - Configure les variables d'environnement pour les services de base de données.
2.  **Modèles et Connexion DB (`agent/agent_db/`)**:
    - `models.py`: Définis les tables PostgreSQL `stocks`, `user_preferences`, `embeddings` avec SQLAlchemy.
    - `database.py`: Implémente la logique de connexion pour PostgreSQL (SQLAlchemy), MongoDB (PyMongo) et Redis (redis-py). Assure-toi d'utiliser des pools de connexion.
3.  **API FastAPI de Base (`agent/main.py`)**:
    - Crée l'application FastAPI.
    - Ajoute un endpoint de health check (`/health`) qui vérifie la connexion aux bases de données.
4.  **Structure de l'Agent LangGraph (`agent/agent_langgraph/`)**:
    - `state.py`: Définis la `TypedDict` `AgentState`.
    - `nodes.py`: Implémente les fonctions pour chaque nœud : `parse_query`, `retrieve_data`, `execute_action`. Initialement, ces fonctions peuvent retourner des données statiques.
    - `graph.py`: Assemble le graphe avec les nœuds et les arêtes conditionnelles.
5.  **Endpoint de l'Agent (`agent/api/routers.py`)**:
    - Crée un endpoint POST `/agent/query` qui accepte une requête utilisateur (`query: str`, `user_id: int`).
    - Ce endpoint invoque le graphe LangGraph et retourne le résultat.
6.  **Sécurité**:
    - Implémente la validation stricte de la sortie JSON du LLM dans `parse_query`.
    - Utilise des requêtes paramétrées avec SQLAlchemy dans `retrieve_data` et `execute_action`. N'exécute JAMAIS de SQL brut généré par le LLM.

### Module 2: Outils de Collecte de Données

**Objectif**: Donner à l'agent la capacité de collecter des données financières depuis des sources externes.

1.  **Création des Outils (`agent/agent_tools/data_collection.py`)**:
    - Implémente les fonctions Python pour interroger chaque API externe (SEC EDGAR, FMP, NewsAPI, yfinance, Finnhub).
    - Chaque fonction doit gérer les erreurs d'API (ex: quotas dépassés, symbole non trouvé).
2.  **Intégration LangChain**:
    - Annote chaque fonction avec le décorateur `@tool` de LangChain.
    - Assure-toi que chaque `tool` a une description claire (`docstring`) expliquant son utilité, ses arguments et ce qu'elle retourne.
3.  **Implémentation du Caching**:
    - Modifie chaque fonction pour qu'elle vérifie d'abord dans Redis si un résultat pour la même requête existe.
    - Si oui, retourne le résultat du cache.
    - Sinon, appelle l'API, stocke le résultat dans Redis avec une expiration (TTL), et retourne le résultat.
4.  **Mise à jour de l'Agent**:
    - Fournis les outils de collecte de données à l'agent pour qu'il puisse les utiliser.

### Module 3: Outils d'Analyse Financière

**Objectif**: Permettre à l'agent d'analyser les données collectées.

1.  **Création des Outils (`agent/agent_tools/financial_analysis.py`)**:
    - Intègre la librairie `Finance-Toolkit`.
    - Crée des fonctions pour les tâches d'analyse : calcul de ratios, analyse de tendances.
    - Ces fonctions prendront en entrée des données structurées (ex: DataFrame Pandas) issues des outils de collecte.
2.  **Intégration LangChain**:
    - Transforme ces fonctions en `tool` LangChain avec des descriptions claires.

### Module 4: Génération de Rapports et Recommandations

**Objectif**: L'agent doit synthétiser toutes les informations pour produire un rapport et des recommandations.

1.  **Nouveau Nœud ou Outil de Synthèse**:
    - Crée un outil ou un nœud LangGraph final dont le rôle est de synthétiser les données.
    - Il prendra en entrée les sorties structurées des outils d'analyse et de collecte.
2.  **Prompt de Synthèse**:
    - Dans ce nœud/outil, utilise un prompt LLM détaillé pour générer un rapport textuel complet et des recommandations d'investissement personnalisées basées sur le profil de l'utilisateur.

### Module 5: Interface Utilisateur avec Chainlit

**Objectif**: Créer une interface web pour interagir avec l'agent.

1.  **Développement de `app/app.py`**:
    - Crée une application Chainlit.
    - L'interface doit permettre à l'utilisateur de saisir une requête.
2.  **Connexion au Backend**:
    - Quand l'utilisateur envoie un message, l'application Chainlit doit faire un appel HTTP POST à l'endpoint `/agent/query` de l'API FastAPI.
3.  **Affichage des Résultats**:
    - Affiche la réponse de l'agent de manière claire et formatée dans l'interface. Gère le streaming si possible pour une meilleure expérience.

---

## 4. Écueils et Bonnes Pratiques (Rappels Cruciaux)

- **Sécurité avant tout**: Valide, nettoie et paramètre TOUTES les entrées vers les bases de données. Fais confiance à ton code, pas à la sortie du LLM.
- **Gestion des Quotas**: Le caching avec Redis n'est pas optionnel, il est obligatoire pour éviter le blocage des API.
- **Normalisation des Données**: Les données de sources multiples seront hétérogènes. Utilise des schémas Pydantic pour les normaliser en un format interne unifié.
- **Tests**: Écris des tests unitaires pour tes outils et des tests d'intégration pour les endpoints de l'API (`/tests/`).
- **Idempotence**: Assure-toi que les opérations de modification de données sont idempotentes lorsque c'est possible.
- **Itération**: Le "prompt engineering" est un processus itératif. Log les prompts et les sorties pour améliorer continuellement la performance de l'agent.
