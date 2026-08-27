from api import (
    get_similar_artists,
    busca_tags_candidatos
)

from database import run_query

from preprocessing import (
    build_tfidf_v3_data,
    build_user_vector,
    normalize_tag
)

import pandas as pd

# Pega os N maiores artistas da matriz_artista
def get_top_artists(matriz_artista_tag, n):
  relevancia_artistas = matriz_artista_tag.sum(axis=1)

  top_artistas = (
      relevancia_artistas
      .sort_values(ascending=False)
      .head(n)
  )

  return top_artistas



# Filtra artistas que já possuem scrobble no banco
def filtrar_artistas_ja_escutados(df, user, db_path):
  query = '''
    SELECT DISTINCT LOWER(TRIM(artista)) AS artista_lower
    FROM plays
    WHERE user = ?
  '''
  artistas_escutados = run_query(
      query,
      db_path,
      (user,)
  )

  artistas_escutados = set(artistas_escutados["artista_lower"])

  df["artista_lower"] = (
      df["candidato"]
      .str.strip()
      .str.lower()
  )

  df = df[
      ~df["artista_lower"].isin(artistas_escutados)
  ].copy()

  df = df.drop(
      columns="artista_lower"
  )

  return df



# Retorna os melhores candidatos
def consolidar_candidatos(
    candidatos_df,
    relevancia_sementes,
    aggfunc='sum',
    retornar_detalhes=False
):
    relevancia_normalizada = _minmax(relevancia_sementes)

    df = candidatos_df.merge(
        relevancia_normalizada.rename('relevancia_norm'),
        left_on='semente',
        right_index=True,
        how='left'
    )

    df['contribuicao'] = (
        df['relevancia_norm']
        * df['match_lastfm']
    )

    score_final = (
        df.groupby('candidato')['contribuicao']
        .agg(aggfunc)
        .rename('score_final')
    )

    n_sementes = (
        df.groupby('candidato')['semente']
        .nunique()
        .rename('n_sementes')
    )

    ranking_final = (
        pd.concat(
            [score_final, n_sementes],
            axis=1
        )
        .sort_values(
            'score_final',
            ascending=False
        )
    )

    if retornar_detalhes:
        return ranking_final, df

    return ranking_final



# Calcula a compatiblidade das tags de acordo com o TFIDF
def calcular_compatibilidade_tags_idf(
    df_tags_candidatos,
    vetor_usuario,
    idf_tags,
    retornar_detalhes=False
):
    relevancia_tags = vetor_usuario.to_dict()

    df = df_tags_candidatos.copy()

    df['tag'] = df['tag'].apply(normalize_tag)
    df = df.dropna(subset=['tag'])

    df['relevancia_usuario'] = (
        df['tag']
        .map(relevancia_tags)
        .fillna(0)
    )

    df['idf'] = (
        df['tag']
        .map(idf_tags)
        .fillna(0)
    )

    df['compatibilidade_tag'] = (
        df['relevancia_usuario']
        * df['idf']
    )

    compatibilidade = (
        df.groupby('artista')['compatibilidade_tag']
        .sum()
        .rename('compatibilidade_tags')
        .sort_values(ascending=False)
    )

    if retornar_detalhes:
        return compatibilidade, df

    return compatibilidade



# Função que normaliza uma série
def _minmax(serie):
  amplitude = serie.max() - serie.min()
  if amplitude == 0:
    return serie * 0

  return (serie - serie.min()) / amplitude



# Função que gera as recomendações de artistas baseado em pesos
def gerar_recomendacoes(
  user, db_path,
  n_sementes=20, n_similares=20, n_candidatos=30,
  half_life_days=180,
  peso_lastfm=0.3, peso_tags=0.7
):

  tfidf_df = build_tfidf_v3_data(user, db_path, half_life_days)
  vetor_usuario, matriz_artista_tag = build_user_vector(tfidf_df)
  top_artistas = get_top_artists(matriz_artista_tag, n_sementes)

  candidatos = get_similar_artists(top_artistas, n_similares)
  if candidatos.empty:
      raise ValueError("Nenhum artista similar foi encontrado para gerar recomendações.")

  candidatos = filtrar_artistas_ja_escutados(candidatos, user, db_path)
  if candidatos.empty:
      raise ValueError("Nenhum candidato novo foi encontrado após remover artistas já escutados.")

  ranking, detalhes_sementes = consolidar_candidatos(candidatos, top_artistas, aggfunc='sum', retornar_detalhes=True)

  top_candidatos = ranking.head(n_candidatos).index.tolist()

  df_tags_candidatos = busca_tags_candidatos(top_candidatos)
  if df_tags_candidatos.empty:
      raise ValueError("Não foi possível obter tags para os candidatos.")

  idf_tags = tfidf_df[['tag', 'idf']].drop_duplicates('tag').set_index('tag')['idf']

  compatibilidade, detalhes_tags = calcular_compatibilidade_tags_idf(df_tags_candidatos, vetor_usuario, idf_tags, retornar_detalhes=True)
  if compatibilidade.empty:
      raise ValueError("Não foi possível calcular compatibilidade de tags.")

  ranking['score_lastfm_norm'] = _minmax(ranking['score_final'])
  ranking['compatibilidade_tags_norm'] = _minmax(compatibilidade)
  ranking['score_recomendacao'] = (
      peso_lastfm * ranking['score_lastfm_norm']
      + peso_tags * ranking['compatibilidade_tags_norm']
  )

  ranking = ranking.sort_values(
      'score_recomendacao',
      ascending=False
  )

  return ranking, detalhes_sementes, detalhes_tags



# Formata as recomendações da tabela ranking
def formatar_recomendacoes(ranking, n=10):
    resultado = (
        ranking
        .head(n)
        .reset_index()
        .rename(columns={
            "candidato": "artista",
            "score_recomendacao": "score"
        })
    )

    resultado["rank"] = range(1, len(resultado) + 1)

    return resultado[
        ["rank", "artista", "score"]
    ]



# Retorna os pesos que explicam as recomendações
def explicar_recomendacao(
    artista,
    detalhes_sementes,
    detalhes_tags,
    n_sementes=3,
    n_tags=3
):
    sementes = (
        detalhes_sementes[
            detalhes_sementes['candidato'] == artista
        ]
        .sort_values(
            'contribuicao',
            ascending=False
        )
        .head(n_sementes)
    )

    tags = (
        detalhes_tags[
            detalhes_tags['artista'] == artista
        ]
        .query('compatibilidade_tag > 0')
        .sort_values(
            'compatibilidade_tag',
            ascending=False
        )
        .head(n_tags)
    )

    return {
        'artista': artista,
        'sementes': sementes['semente'].tolist(),
        'tags': tags['tag'].tolist()
    }