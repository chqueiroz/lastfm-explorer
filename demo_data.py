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
def carregar_scrobbles_ao_longo_tempo(dias=None):
    with sqlite3.connect(DEMO_DB_PATH) as conn:

        if dias is None:
            # Histórico completo → mensal
            query = """
            SELECT
                strftime('%Y-%m-01', data_hora) AS periodo,
                COUNT(*) AS total
            FROM plays
            WHERE user = ?
            GROUP BY periodo
            ORDER BY periodo
            """

            params = (DEMO_USER,)

        elif dias <= 30:
            # 30 dias → diário
            query = """
            SELECT
                strftime('%Y-%m-%d', data_hora) AS periodo,
                COUNT(*) AS total
            FROM plays
            WHERE user = ?
              AND uts >= (
                  SELECT MAX(uts) - ?
                  FROM plays
                  WHERE user = ?
              )
            GROUP BY periodo
            ORDER BY periodo
            """

            params = (
                DEMO_USER,
                dias * 86400,
                DEMO_USER
            )

        elif dias <= 90:
            # 90 dias → semanal
            query = """
            SELECT
                date(
                    data_hora,
                    printf(
                        '-%d days',
                        (CAST(strftime('%w', data_hora) AS INTEGER) + 6) % 7
                    )
                ) AS periodo,
                COUNT(*) AS total
            FROM plays
            WHERE user = ?
              AND uts >= (
                  SELECT MAX(uts) - ?
                  FROM plays
                  WHERE user = ?
              )
            GROUP BY periodo
            ORDER BY periodo
            """

            params = (
                DEMO_USER,
                dias * 86400,
                DEMO_USER
            )

        else:
            # 1 ano → mensal
            query = """
            SELECT
                strftime('%Y-%m-01', data_hora) AS periodo,
                COUNT(*) AS total
            FROM plays
            WHERE user = ?
              AND uts >= (
                  SELECT MAX(uts) - ?
                  FROM plays
                  WHERE user = ?
              )
            GROUP BY periodo
            ORDER BY periodo
            """

            params = (
                DEMO_USER,
                dias * 86400,
                DEMO_USER
            )

        return pd.read_sql_query(
            query,
            conn,
            params=params
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
def carregar_scrobbles_por_dia_semana(dias=None):
    with sqlite3.connect(DEMO_DB_PATH) as conn:

        if dias is None:
            query = """
            SELECT
                strftime('%w', data_hora) AS dia,
                COUNT(*) AS total
            FROM plays
            WHERE user = ?
            GROUP BY dia
            ORDER BY dia
            """

            params = (DEMO_USER,)

        else:
            query = """
            SELECT
                strftime('%w', data_hora) AS dia,
                COUNT(*) AS total
            FROM plays
            WHERE user = ?
              AND uts >= (
                  SELECT MAX(uts) - ?
                  FROM plays
                  WHERE user = ?
              )
            GROUP BY dia
            ORDER BY dia
            """

            params = (
                DEMO_USER,
                dias * 86400,
                DEMO_USER
            )

        df = pd.read_sql_query(
            query,
            conn,
            params=params
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
def carregar_scrobbles_por_hora(dias=None):
    with sqlite3.connect(DEMO_DB_PATH) as conn:

        if dias is None:
            query = """
            SELECT
                strftime('%H', data_hora) AS hora,
                COUNT(*) AS total
            FROM plays
            WHERE user = ?
            GROUP BY hora
            ORDER BY hora
            """

            params = (DEMO_USER,)

        else:
            query = """
            SELECT
                strftime('%H', data_hora) AS hora,
                COUNT(*) AS total
            FROM plays
            WHERE user = ?
              AND uts >= (
                  SELECT MAX(uts) - ?
                  FROM plays
                  WHERE user = ?
              )
            GROUP BY hora
            ORDER BY hora
            """

            params = (
                DEMO_USER,
                dias * 86400,
                DEMO_USER
            )

        return pd.read_sql_query(
            query,
            conn,
            params=params
        )


@st.cache_data
def carregar_descobertas_recentes(dias=None):
    with sqlite3.connect(DEMO_DB_PATH) as conn:

        if dias is None:
            query = """
            SELECT
                artista,
                MIN(uts) AS primeiro_scrobble
            FROM plays
            WHERE user = ?
            GROUP BY artista
            ORDER BY primeiro_scrobble DESC
            """

            params = (DEMO_USER,)

        else:
            query = """
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
            """

            params = (
                DEMO_USER,
                dias * 86400,
                DEMO_USER
            )

        df = pd.read_sql_query(
            query,
            conn,
            params=params
        )

    df["data_descoberta"] = pd.to_datetime(
        df["primeiro_scrobble"],
        unit="s",
        utc=True,
        errors="coerce"
    )

    df = df.dropna(subset=["data_descoberta"])

    df["data_descoberta"] = (
        df["data_descoberta"]
        .dt.tz_convert("America/Sao_Paulo")
        .dt.date
    )

    return df[
        ["artista", "data_descoberta"]
    ]


@st.cache_data
def carregar_variacao_scrobbles(dias):
    segundos = dias * 86400

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
                segundos,
                DEMO_USER,
                segundos * 2,
                segundos
            )
        )

    atual = int(df.iloc[0]["total_atual"])
    anterior = int(df.iloc[0]["total_anterior"])

    variacao = (
        ((atual - anterior) / anterior) * 100
        if anterior > 0
        else None
    )

    return atual, anterior, variacao


@st.cache_data
def carregar_hora_mais_ativa(dias=None):
    with sqlite3.connect(DEMO_DB_PATH) as conn:

        if dias is None:
            query = """
            SELECT
                strftime('%H', data_hora) AS hora,
                COUNT(*) AS total
            FROM plays
            WHERE user = ?
            GROUP BY hora
            ORDER BY total DESC
            LIMIT 1
            """

            params = (DEMO_USER,)

        else:
            query = """
            SELECT
                strftime('%H', data_hora) AS hora,
                COUNT(*) AS total
            FROM plays
            WHERE user = ?
              AND uts >= (
                  SELECT MAX(uts) - ?
                  FROM plays
                  WHERE user = ?
              )
            GROUP BY hora
            ORDER BY total DESC
            LIMIT 1
            """

            params = (
                DEMO_USER,
                dias * 86400,
                DEMO_USER
            )

        df = pd.read_sql_query(
            query,
            conn,
            params=params
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


@st.cache_data
def carregar_scrobbles_por_periodo_dia(dias=None):
    with sqlite3.connect(DEMO_DB_PATH) as conn:

        if dias is None:
            filtro_periodo = ""
            params = (DEMO_USER,)

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
                DEMO_USER
            )

        query = f"""
        SELECT
            CASE
                WHEN CAST(strftime('%H', data_hora) AS INTEGER) BETWEEN 0 AND 5
                    THEN 'Madrugada'
                WHEN CAST(strftime('%H', data_hora) AS INTEGER) BETWEEN 6 AND 11
                    THEN 'Manhã'
                WHEN CAST(strftime('%H', data_hora) AS INTEGER) BETWEEN 12 AND 17
                    THEN 'Tarde'
                ELSE 'Noite'
            END AS periodo,
            COUNT(*) AS total
        FROM plays
        WHERE user = ?
        {filtro_periodo}
        GROUP BY periodo
        """

        return pd.read_sql_query(
            query,
            conn,
            params=params
        )