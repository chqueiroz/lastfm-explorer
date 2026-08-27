import sqlite3

import pandas as pd
import streamlit as st

from config import DEMO_DB_PATH, DEMO_USER


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


@st.cache_data
def carregar_total_scrobbles():
    with sqlite3.connect(DEMO_DB_PATH) as conn:
        df = pd.read_sql_query(
            """
            SELECT COUNT(*) AS total
            FROM plays
            WHERE user = ?
            """,
            conn,
            params=(DEMO_USER,)
        )

    return int(df.iloc[0]["total"])


@st.cache_data
def carregar_total_artistas():
    with sqlite3.connect(DEMO_DB_PATH) as conn:
        df = pd.read_sql_query(
            """
            SELECT COUNT(DISTINCT artista) AS total
            FROM plays
            WHERE user = ?
            """,
            conn,
            params=(DEMO_USER,)
        )

    return int(df.iloc[0]["total"])


@st.cache_data
def carregar_top_artistas(limit=10, dias=None):
    with sqlite3.connect(DEMO_DB_PATH) as conn:

        if dias is None:
            query = """
            SELECT artista, COUNT(*) AS total
            FROM plays
            WHERE user = ?
            GROUP BY artista
            ORDER BY total DESC
            LIMIT ?
            """

            params = (DEMO_USER, limit)

        else:
            query = """
            SELECT artista, COUNT(*) AS total
            FROM plays
            WHERE user = ?
              AND uts >= (
                  SELECT MAX(uts) - ?
                  FROM plays
                  WHERE user = ?
              )
            GROUP BY artista
            ORDER BY total DESC
            LIMIT ?
            """

            params = (
                DEMO_USER,
                dias * 86400,
                DEMO_USER,
                limit
            )

        return pd.read_sql_query(
            query,
            conn,
            params=params
        )


@st.cache_data
def carregar_scrobbles_por_mes():
    with sqlite3.connect(DEMO_DB_PATH) as conn:
        return pd.read_sql_query(
            """
            SELECT
                strftime('%Y-%m', data_hora) AS mes,
                COUNT(*) AS total
            FROM plays
            WHERE user = ?
            GROUP BY mes
            ORDER BY mes
            """,
            conn,
            params=(DEMO_USER,)
        )


@st.cache_data
def carregar_scrobbles_por_ano():
    with sqlite3.connect(DEMO_DB_PATH) as conn:
        return pd.read_sql_query(
            """
            SELECT
                strftime('%Y', data_hora) AS ano,
                COUNT(*) AS total
            FROM plays
            WHERE user = ?
            GROUP BY ano
            ORDER BY ano
            """,
            conn,
            params=(DEMO_USER,)
        )


@st.cache_data
def carregar_scrobbles_por_dia_semana():
    with sqlite3.connect(DEMO_DB_PATH) as conn:
        df = pd.read_sql_query(
            """
            SELECT
                strftime('%w', data_hora) AS dia,
                COUNT(*) AS total
            FROM plays
            WHERE user = ?
            GROUP BY dia
            ORDER BY dia
            """,
            conn,
            params=(DEMO_USER,)
        )

    dias_map = {
        "0": "Domingo",
        "1": "Segunda",
        "2": "Terça",
        "3": "Quarta",
        "4": "Quinta",
        "5": "Sexta",
        "6": "Sábado"
    }

    df["dia"] = df["dia"].map(dias_map)

    return df


@st.cache_data
def carregar_scrobbles_por_hora():
    with sqlite3.connect(DEMO_DB_PATH) as conn:
        return pd.read_sql_query(
            """
            SELECT
                strftime('%H', data_hora) AS hora,
                COUNT(*) AS total
            FROM plays
            WHERE user = ?
            GROUP BY hora
            ORDER BY hora
            """,
            conn,
            params=(DEMO_USER,)
        )


@st.cache_data
def carregar_descobertas_recentes(dias=30):
    with sqlite3.connect(DEMO_DB_PATH) as conn:

        df = pd.read_sql_query(
            """
            SELECT
                artista,
                MIN(uts) AS primeiro_scrobble
            FROM plays
            WHERE user = ?
            GROUP BY artista
            HAVING primeiro_scrobble >= (
                SELECT MAX(uts) - ?
                FROM plays
                WHERE user = ?
            )
            ORDER BY primeiro_scrobble DESC
            """,
            conn,
            params=(
                DEMO_USER,
                dias * 24 * 60 * 60,
                DEMO_USER
            )
        )

    df["data_descoberta"] = (
        pd.to_datetime(
            df["primeiro_scrobble"],
            unit="s",
            utc=True
        )
        .dt.tz_convert("America/Sao_Paulo")
        .dt.strftime("%d/%m/%Y")
    )

    return df[
        ["artista", "data_descoberta"]
    ]


@st.cache_data
def carregar_variacao_scrobbles(dias=30):
    with sqlite3.connect(DEMO_DB_PATH) as conn:
        df = pd.read_sql_query(
            """
            WITH referencia AS (
                SELECT MAX(uts) AS max_uts
                FROM plays
                WHERE user = ?
            ),
            atual AS (
                SELECT COUNT(*) AS total_atual
                FROM plays, referencia
                WHERE user = ?
                  AND uts > max_uts - ?
            ),
            anterior AS (
                SELECT COUNT(*) AS total_anterior
                FROM plays, referencia
                WHERE user = ?
                  AND uts > max_uts - ?
                  AND uts <= max_uts - ?
            )
            SELECT
                atual.total_atual,
                anterior.total_anterior
            FROM atual, anterior
            """,
            conn,
            params=(
                DEMO_USER,
                DEMO_USER,
                dias * 86400,
                DEMO_USER,
                dias * 2 * 86400,
                dias * 86400
            )
        )

    atual = int(df.iloc[0]["total_atual"])
    anterior = int(df.iloc[0]["total_anterior"])

    if anterior == 0:
        variacao = None
    else:
        variacao = ((atual - anterior) / anterior) * 100

    return atual, anterior, variacao


@st.cache_data
def carregar_hora_mais_ativa():
    with sqlite3.connect(DEMO_DB_PATH) as conn:
        df = pd.read_sql_query(
            """
            SELECT
                strftime('%H', data_hora) AS hora,
                COUNT(*) AS total
            FROM plays
            WHERE user = ?
            GROUP BY hora
            ORDER BY total DESC
            LIMIT 1
            """,
            conn,
            params=(DEMO_USER,)
        )

    return df.iloc[0]["hora"], int(df.iloc[0]["total"])



@st.cache_data
def carregar_top_albuns(limit=10, dias=None):
    with sqlite3.connect(DEMO_DB_PATH) as conn:

        if dias is None:
            query = """
            SELECT album, artista, COUNT(*) AS total
            FROM plays
            WHERE user = ?
              AND album IS NOT NULL
              AND TRIM(album) <> ''
            GROUP BY album, artista
            ORDER BY total DESC
            LIMIT ?
            """

            params = (DEMO_USER, limit)

        else:
            query = """
            SELECT album, artista, COUNT(*) AS total
            FROM plays
            WHERE user = ?
              AND album IS NOT NULL
              AND TRIM(album) <> ''
              AND uts >= (
                  SELECT MAX(uts) - ?
                  FROM plays
                  WHERE user = ?
              )
            GROUP BY album, artista
            ORDER BY total DESC
            LIMIT ?
            """

            params = (
                DEMO_USER,
                dias * 86400,
                DEMO_USER,
                limit
            )

        return pd.read_sql_query(
            query,
            conn,
            params=params
        )


@st.cache_data
def carregar_top_faixas(limit=10, dias=None):
    with sqlite3.connect(DEMO_DB_PATH) as conn:

        if dias is None:
            query = """
            SELECT faixa, artista, COUNT(*) AS total
            FROM plays
            WHERE user = ?
            GROUP BY faixa, artista
            ORDER BY total DESC
            LIMIT ?
            """

            params = (DEMO_USER, limit)

        else:
            query = """
            SELECT faixa, artista, COUNT(*) AS total
            FROM plays
            WHERE user = ?
              AND uts >= (
                  SELECT MAX(uts) - ?
                  FROM plays
                  WHERE user = ?
              )
            GROUP BY faixa, artista
            ORDER BY total DESC
            LIMIT ?
            """

            params = (
                DEMO_USER,
                dias * 86400,
                DEMO_USER,
                limit
            )

        return pd.read_sql_query(
            query,
            conn,
            params=params
        )


@st.cache_data
def carregar_variacao_novos_artistas(dias=30):
    segundos = dias * 24 * 60 * 60

    with sqlite3.connect(DEMO_DB_PATH) as conn:
        df = pd.read_sql_query(
            """
            WITH referencia AS (
                SELECT MAX(uts) AS max_uts
                FROM plays
                WHERE user = ?
            ),
            primeira_escuta AS (
                SELECT
                    artista,
                    MIN(uts) AS primeiro_scrobble
                FROM plays
                WHERE user = ?
                GROUP BY artista
            )
            SELECT
                SUM(
                    CASE
                        WHEN primeiro_scrobble > max_uts - ?
                        THEN 1 ELSE 0
                    END
                ) AS novos_atual,

                SUM(
                    CASE
                        WHEN primeiro_scrobble > max_uts - ?
                         AND primeiro_scrobble <= max_uts - ?
                        THEN 1 ELSE 0
                    END
                ) AS novos_anterior

            FROM primeira_escuta, referencia
            """,
            conn,
            params=(
                DEMO_USER,
                DEMO_USER,
                segundos,
                segundos * 2,
                segundos
            )
        )

    atual = int(df.iloc[0]["novos_atual"])
    anterior = int(df.iloc[0]["novos_anterior"])

    if anterior == 0:
        variacao = None
    else:
        variacao = ((atual - anterior) / anterior) * 100

    return atual, anterior, variacao


@st.cache_data
def carregar_top_tags(limit=10, dias=None):
    with sqlite3.connect(DEMO_DB_PATH) as conn:

        if dias is None:
            filtro_periodo = ""
            params = (DEMO_USER, limit)

        else:
            filtro_periodo = """
              AND uts >= (
                  SELECT MAX(uts) - ?
                  FROM plays
                  WHERE user = ?
              )
            """

            params = (
                DEMO_USER,
                dias * 86400,
                DEMO_USER,
                limit
            )

        query = f"""
        WITH plays_artista AS (
            SELECT
                LOWER(TRIM(artista)) AS artista_lower,
                COUNT(*) AS total_plays
            FROM plays
            WHERE user = ?
            {filtro_periodo}
            GROUP BY artista_lower
        ),

        tags AS (
            SELECT
                LOWER(TRIM(artista)) AS artista_lower,
                tag,
                peso,
                SUM(peso) OVER (
                    PARTITION BY LOWER(TRIM(artista))
                ) AS peso_total
            FROM artist_tags_normalized
        )

        SELECT
            tag,
            SUM(
                total_plays *
                (CAST(peso AS REAL) / peso_total)
            ) AS relevancia
        FROM tags
        JOIN plays_artista USING (artista_lower)

        WHERE peso_total > 0

        GROUP BY tag
        ORDER BY relevancia DESC
        LIMIT ?
        """

        return pd.read_sql_query(
            query,
            conn,
            params=params
        )



@st.cache_data
def carregar_evolucao_tags(limit=5, dias=None):
    with sqlite3.connect(DEMO_DB_PATH) as conn:

        if dias is None:
            filtro_periodo = ""

            params = (
                DEMO_USER,
                limit
            )

        else:
            filtro_periodo = """
                AND p.uts >= (
                    SELECT MAX(uts) - ?
                    FROM plays
                    WHERE user = ?
                )
            """

            params = (
                DEMO_USER,
                dias * 86400,
                DEMO_USER,
                limit
            )

        query = f"""
        WITH tags AS (
            SELECT
                LOWER(TRIM(artista)) AS artista_lower,
                tag,
                peso,
                SUM(peso) OVER (
                    PARTITION BY LOWER(TRIM(artista))
                ) AS peso_total
            FROM artist_tags_normalized
        ),

        plays_tags AS (
            SELECT
                strftime('%Y-%m', p.data_hora) AS mes,
                LOWER(TRIM(p.artista)) AS artista_lower,
                t.tag,
                CAST(t.peso AS REAL) / t.peso_total AS peso_tag
            FROM plays AS p
            JOIN tags AS t
                ON LOWER(TRIM(p.artista)) = t.artista_lower
            WHERE p.user = ?
              AND t.peso_total > 0
              {filtro_periodo}
        ),

        relevancia_total AS (
            SELECT
                tag,
                SUM(peso_tag) AS relevancia
            FROM plays_tags
            GROUP BY tag
            ORDER BY relevancia DESC
            LIMIT ?
        )

        SELECT
            pt.mes,
            pt.tag,
            SUM(pt.peso_tag) AS relevancia
        FROM plays_tags AS pt
        JOIN relevancia_total AS rt
            ON pt.tag = rt.tag
        GROUP BY pt.mes, pt.tag
        ORDER BY pt.mes
        """

        return pd.read_sql_query(
            query,
            conn,
            params=params
        )