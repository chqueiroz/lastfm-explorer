import re
import sqlite3

import numpy as np
import pandas as pd

from database import run_query


# Normalização de tags dos artistas
def normalize_tag(tag):
    if pd.isna(tag):
        return None

    tag = str(tag).strip().lower()
    tag = re.sub(r"\s+", " ", tag)

    if not tag:
        return None

    return tag



# Atualiza as tags normalizadas no DB
def sync_normalized_tags(db_path):
  query = '''
  SELECT artista, tag, peso
  FROM artist_tags
  '''
  df = run_query(query, db_path)

  df['tag'] = df['tag'].apply(normalize_tag)
  df = df.dropna(subset=['tag'])

  df = (
      df.groupby(['artista', 'tag'], as_index=False)['peso']
      .max()
  )

  with sqlite3.connect(db_path) as conn:
    conn.execute("DELETE FROM artist_tags_normalized")
    df.to_sql(
        name='artist_tags_normalized',
        con=conn,
        if_exists='append',
        index=False
    )

  print(f"Tags normalizadas: {len(df)} registros.")



# Calcula o peso de recência de cada play.
def calcular_peso_recencia(data_play, half_life_days=180):
  data_play = pd.to_datetime(
      data_play,
      utc=True
  )
  agora = pd.Timestamp.now(tz="UTC")
  idade_dias = (
      agora - data_play
  ).dt.total_seconds() / (60 * 60 * 24)

  peso_recencia = 0.5 ** (
      idade_dias / half_life_days
  )
  return peso_recencia



# Calcula o TFIDF dos artistas
def build_tfidf_v3_data(user, db_path, half_life_days=180):
  # 1. Busca tags normalizadas dos artistas
  query_tags = '''
  SELECT
      at.artista,
      at.tag,
      at.peso
  FROM artist_tags_normalized AS at
  '''
  df_tags = run_query(query_tags, db_path)

  # 2. Busca plays individuais do usuário
  query_plays = '''
  SELECT
      artista,
      data_hora
  FROM plays
  WHERE user = ?
  '''

  df_plays = run_query(
      query_plays,
      db_path,
      params=(user,)
  )

  # 3. Calcula peso de recência de cada play
  df_plays["peso_recencia"] = calcular_peso_recencia(
      df_plays["data_hora"],
      half_life_days
  )

  # 4. Soma os plays ponderados por artista
  plays_ponderados = (
      df_plays
      .groupby(
          df_plays["artista"].str.strip().str.lower()
      )["peso_recencia"]
      .sum()
      .rename("plays_ponderados")
  )

  # 5. Normaliza nome do artista para fazer o JOIN
  df_tags["artista_lower"] = (
      df_tags["artista"]
      .str.strip()
      .str.lower()
  )

  # 6. Junta tags + plays ponderados
  df = df_tags.merge(
      plays_ponderados,
      left_on="artista_lower",
      right_index=True,
      how="inner"
  )

  if df.empty:
      raise ValueError(
          "Não foi possível construir o perfil musical do usuário."
      )

  # 7. Número total de artistas
  N = df["artista"].nunique()

  # 8. Soma dos pesos das tags de cada artista
  df["peso_total_artista"] = (
      df.groupby("artista")["peso"]
      .transform("sum")
  )

  # 9. Peso relativo da tag dentro do artista
  df["peso_relativo"] = (
      df["peso"] /
      df["peso_total_artista"]
  )

  # 10. Log dos plays ponderados
  df["log_plays"] = np.log1p(
      df["plays_ponderados"]
  )

  # 11. Peso antes do IDF-
  df["peso_final"] = (
      df["peso_relativo"] *
      df["log_plays"]
  )

  # 12. Número de artistas que possuem cada tag
  n_tag = (
      df.groupby("tag")["artista"]
      .nunique()
      .rename("n_tag")
  )

  df = df.merge(
      n_tag,
      on="tag",
      how="left"
  )

  # 13. IDF
  df["idf"] = np.log(
      N / df["n_tag"]
  )

  # 14. TF-IDF final
  df["peso_tfidf"] = (
      df["peso_final"] *
      df["idf"]
  )

  return df



# Função que retorna o vetor do usuário
def build_user_vector(df):
  matriz_artista_tag = df.pivot_table(
      index="artista",
      columns="tag",
      values="peso_tfidf",
      aggfunc="sum",
      fill_value=0
  )

  vetor_usuario = matriz_artista_tag.sum(axis=0)

  return vetor_usuario, matriz_artista_tag