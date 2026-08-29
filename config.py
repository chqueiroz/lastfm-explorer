import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


# API
API_KEY = os.getenv("LASTFM_API_KEY")
USER_AGENT = os.getenv("LASTFM_USER_AGENT")

DEFAULT_RETRIES = 3


# Dados
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "lastfm.db"

DEMO_DB_PATH = DATA_DIR / "demo.db"
DEMO_USER = "chqueiroz"


# Parâmetros do recomendador V3
N_SEMENTES = 20
N_SIMILARES = 20
N_CANDIDATOS = 30

HALF_LIFE_DAYS = 180

PESO_LASTFM = 0.3
PESO_TAGS = 0.7

N_RECOMENDACOES = 10


if abs((PESO_LASTFM + PESO_TAGS) - 1.0) > 1e-9:
    raise ValueError(
        "PESO_LASTFM + PESO_TAGS deve ser igual a 1."
    )