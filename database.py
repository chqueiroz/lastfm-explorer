import sqlite3

import pandas as pd

from config import DB_PATH
from api import (
    download_scrobbles,
    get_sync_snapshot,
    fetch_lastfm_data
)
from config import API_KEY, DEFAULT_RETRIES



# Inicia o db
def initialize_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    faixa TEXT,
    album TEXT,
    artista TEXT,
    mbid_artista TEXT,
    uts INTEGER,
    data_hora TEXT
);
""")

    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_plays_unique
    ON plays (user, uts, artista, faixa);
""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS artist_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artista TEXT,
    tag TEXT,
    peso INTEGER
);
""")

    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_artist_tag_unique
    ON artist_tags (artista, tag);
""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS artist_tags_normalized (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artista TEXT NOT NULL,
    tag TEXT NOT NULL,
    peso INTEGER
)
""")

    cursor.execute("""
CREATE UNIQUE INDEX IF NOT EXISTS idx_artist_tag_normalized_unique
ON artist_tags_normalized (artista, tag);
""")

    conn.commit()
    return conn



# Pega o uts da faixa mais recente salva no db
def get_latest_uts(conn, user):
  cursor = conn.cursor()
  cursor.execute(
        """
        SELECT MAX(uts)
        FROM plays
        WHERE user = ?
        LIMIT 1
  """, (user,))
  db_latest_uts = cursor.fetchone()[0]

  if db_latest_uts:
    return db_latest_uts
  else:
    return None



# Pega os artistas únicos no db
def get_unique_artists(user, db_path):
  query = '''
    SELECT DISTINCT artista
    FROM plays
    WHERE user = ?
'''
  return run_query(query, db_path, params=(user,))



# Função que sincroniza o db (baixa todos scrobbles ou apenas os que faltam)
def sync_data(conn, user):
  latest_uts = get_latest_uts(conn, user)
  sync_to_uts = get_sync_snapshot(user)

  if latest_uts is None:
    result = download_scrobbles(user, sync_to_uts)
  else:
    result = download_scrobbles(user, sync_to_uts, latest_uts)

  if result is None:
    return

  df = result["df"]
  total_scrobbles = result["total_scrobbles"]
  paginas_com_erro_final = result["paginas_com_erro_final"]

  if paginas_com_erro_final:
    print("Páginas falharam após todas tentativas. Encerrando...")
    print(paginas_com_erro_final)
    return

  else:
    print("Todas as páginas foram salvas.")

  df.to_sql(
      name="plays",
      con=conn,
      if_exists="append",
      index=False
  )

  print("Sincronização concluída.")
  print(f"{total_scrobbles} scrobbles. {len(df)} registros salvos. ({round(len(df)/total_scrobbles*100, 2)}%)")



# Função que sincroniza as tags dos artistas únicos de um usuário do db (baixa todas as tags ou apenas as que faltam)
def sync_artist_tags(user, db_path):
  df_unique_artists = get_unique_artists(user, db_path)

  lista_artist_tag = []
  artist_tag_com_erro = []
  artist_tag_com_erro_final = []
  cont_art = 1
  tamanho = len(df_unique_artists)

  for artista in df_unique_artists['artista']:
    print(f"Baixando: {artista}")
    query = '''
        SELECT 1
        FROM artist_tags
        WHERE artista = ?
        LIMIT 1;
    '''
    df = run_query(query, db_path, (f'{artista}',))
    if df.empty:
      loop_params = {
          "method": "artist.gettoptags",
          "artist": artista
      }
      data = fetch_lastfm_data(API_KEY, loop_params, DEFAULT_RETRIES)
      if data:
        if data['toptags']['tag']:
          print(f"Nome: {artista}")
          cont = 1
          for tag in data['toptags']['tag']:
            if cont > 5:
              break
            lista_artist_tag.append(
              {
                  "artista": artista,
                  "tag": tag['name'],
                  "peso": tag['count']
              }
          )
            cont += 1
        else:
          lista_artist_tag.append(
              {
                  "artista": artista,
                  "tag": None,
                  "peso": None
              }
          )

      else:
        artist_tag_com_erro.append(artista)

    else:
      print(f"OK. {cont_art}/{tamanho} ({round(cont_art/tamanho*100, 2)}%).\n")
      cont_art += 1
      continue

    print(f"OK. {cont_art}/{tamanho} ({round(cont_art/tamanho*100, 2)}%).\n")
    cont_art += 1



  if artist_tag_com_erro:
    print("\nExistem artistas com erro! Tentando novamente...")
    for artista in artist_tag_com_erro:
      print(f"Testando novamente artista: {artista}")
      query = '''
          SELECT 1
          FROM artist_tags
          WHERE artista = ?
          LIMIT 1;
      '''
      df = run_query(query, db_path, (f'{artista}',))
      if df.empty:
        loop_params = {
            "method": "artist.gettoptags",
            "artist": artista
        }
        data = fetch_lastfm_data(API_KEY, loop_params, DEFAULT_RETRIES)
        if data:
          if data['toptags']['tag']:
            cont = 1
            for tag in data['toptags']['tag']:
              if cont > 5:
                break
              lista_artist_tag.append(
                {
                    "artista": artista,
                    "tag": tag['name'],
                    "peso": tag['count']
                }
            )
              cont += 1
          else:
            lista_artist_tag.append(
                {
                    "artista": artista,
                    "tag": None,
                    "peso": None
                }
            )
        else:
          artist_tag_com_erro_final.append(artista)

  if artist_tag_com_erro_final:
    print("Artistas que falharam:")
    print(artist_tag_com_erro_final)
  else:
    print("Todos os artistas foram salvos.")


  if not lista_artist_tag:
    print("Nenhuma nova tag para salvar.")
    return

  conn = sqlite3.connect(db_path)
  df_final = pd.DataFrame(lista_artist_tag)

  duplicatas = df_final.duplicated(
    subset=['artista', 'tag']
).sum()

  if duplicatas > 0:
    print(f"Duplicatas removidas: {duplicatas}")
    df_final = df_final.drop_duplicates(
        subset=['artista', 'tag']
    )

  df_final.to_sql(
      name="artist_tags",
      con=conn,
      if_exists="append",
      index=False
  )

  conn.close()
  print("Sincronização concluída.")



# Função genérica para chamadas SQL
def run_query(sql, db_path, params=None):
  with sqlite3.connect(db_path) as conn:
    df = pd.read_sql_query(sql, conn, params=params)
  return df



# Conta quantos scrobbles do usuário tem salvos
def contar_scrobbles(user, db_path):
    query = '''
    SELECT COUNT(*) AS total
    FROM plays
    WHERE user = ?
    '''

    df = run_query(query, db_path, params=(user,))

    return int(df.iloc[0]['total'])