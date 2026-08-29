import sqlite3

import pandas as pd
import streamlit as st

from config import DEMO_DB_PATH


@st.cache_data
def carregar_recomendacoes_demo():
    with sqlite3.connect(DEMO_DB_PATH) as conn:
        return pd.read_sql_query(
            """
            SELECT rank, artista, score
            FROM demo_recomendacoes
            ORDER BY rank
            """,
            conn
        )


@st.cache_data
def carregar_sementes_demo():
    with sqlite3.connect(DEMO_DB_PATH) as conn:
        return pd.read_sql_query(
            """
            SELECT artista, semente, match_lastfm, contribuicao
            FROM demo_sementes
            """,
            conn
        )


@st.cache_data
def carregar_tags_demo():
    with sqlite3.connect(DEMO_DB_PATH) as conn:
        return pd.read_sql_query(
            """
            SELECT artista, tag, compatibilidade
            FROM demo_tags
            """,
            conn
        )