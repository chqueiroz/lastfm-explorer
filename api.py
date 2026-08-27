from time import sleep

import pandas as pd
import requests

from config import API_KEY, USER_AGENT, DEFAULT_RETRIES


# Cria uma sessão customizada para as requisições da API
session = requests.Session()
session.headers.update({
    "User-Agent": USER_AGENT
})


# Função genérica para chamadas da API com tratamento de erro e retry
def fetch_lastfm_data(api_key, esp_params, retries):
  url = "https://ws.audioscrobbler.com/2.0/"

  erros_to_retry = (8, 11, 16, 29)
  total_retry = retries
  backoff = 1
  default_params = {
            "api_key": api_key,
            "format": "json"
        }

  curr_try = 1
  while curr_try <= total_retry:
    if curr_try > 1:
      print(f"Tentativa n° {curr_try} de resposta.")
    try:
      request_params = {**default_params, **esp_params}
      sleep(0.25)
      response = session.get(url, params=request_params)

      if response.status_code == 200:
        data = response.json()
        if "error" not in data:
          return data
        else:
          if data["error"] in erros_to_retry:
            raise requests.exceptions.RequestException(f"ERRO {data['error']}: {data['message']}")
          else:
            print(f"ERRO {data['error']}: {data['message']}")
            return None
      else:
        print(f"ERRO na requisição. ({response.status_code})")
        return None

    except requests.exceptions.RequestException as e:
      print(f"Erro de conexão: {e}")
      curr_try += 1
      sleep(backoff)
      backoff *= 2

  else:
    print(f"Erro na requisição.")
    return None



# Verifica se o usuário existe no lastfm
def get_valid_user():
    while True:
        user_validation = input("Digite o usuário do lastfm: ")
        user_validation_params = {
            "user": user_validation,
            "method": "user.getinfo"
        }
        data = fetch_lastfm_data(API_KEY, user_validation_params, DEFAULT_RETRIES)
        if data:
            return user_validation
        print("Não foi possível localizar esse usuário no Last.fm.")



# Pega o uts do scrobble mais recente da API para usar como base de referência (snapshot) de download
def get_sync_snapshot(user):
  sync_snapshot_params = {
          "method": "user.getrecenttracks",
          "user": user,
          "limit": 1,
          "page": 1
      }
  data = fetch_lastfm_data(API_KEY, sync_snapshot_params, DEFAULT_RETRIES)
  if data:
    for track in data['recenttracks']['track']:
      if "date" in track:
        return int(track['date']['uts'])

  return None



# Faz o download de todos os scrobbles de acordo com a faixa de referência (from, to)
def download_scrobbles(user, to_uts, from_uts=None):
  params = {
          "method": "user.getrecenttracks",
          "user": user,
          "limit": 200,
          "page": 1,
          "to": to_uts+1
      }

  if from_uts is not None:
    params["from"] = from_uts+1

  data = fetch_lastfm_data(API_KEY, params, DEFAULT_RETRIES)

  if data:
    print(f"Total de páginas: {data['recenttracks']['@attr']['totalPages']}")
    total_pages = int(data['recenttracks']['@attr']['totalPages'])
    total_scrobbles = int(data['recenttracks']['@attr']['total'])
    if total_pages == 0:
      print("Nenhum novo scrobble encontrado.")
      return
  else:
    print("ERRO inesperado. Encerrando o script...")
    return

  lista_scrobbles = []
  current_page = 1
  paginas_com_erro = []
  paginas_com_erro_final = []

  while current_page <= total_pages:
    print(f"Página: {current_page}/{total_pages}")

    loop_params = {
          **params,
          "page": current_page
      }

    data = fetch_lastfm_data(API_KEY, loop_params, DEFAULT_RETRIES)

    if data:
      for track in data['recenttracks']['track']:
        if "date" in track:
          lista_scrobbles.append(
          {
              "user": user,
              "faixa": track['name'],
              "album": track['album']['#text'],
              "artista": track['artist']['#text'],
              "mbid_artista": track['artist']['mbid'],
              "uts": track['date']['uts']
          }
      )

    else:
      print(f"Erro ao salvar a página {current_page}")
      paginas_com_erro.append(current_page)

    current_page += 1


  if paginas_com_erro:
    print("\nExistem páginas com erro! Tentando novamente...")
    for page in paginas_com_erro:
      print(f"Testando página {page}")
      retry_params = {
          **params,
          "page": page
      }

      data = fetch_lastfm_data(API_KEY, retry_params, DEFAULT_RETRIES)
      if data:
        for track in data['recenttracks']['track']:
          if "date" in track:
            lista_scrobbles.append(
            {
                "user": user,
                "faixa": track['name'],
                "album": track['album']['#text'],
                "artista": track['artist']['#text'],
                "mbid_artista": track['artist']['mbid'],
                "uts": track['date']['uts']
            }
        )
      else:
        paginas_com_erro_final.append(page)

  if not lista_scrobbles:
    print("Falha ao baixar os scrobbles. Todas as páginas da sincronização falharam.")
    return None


  df = pd.DataFrame(lista_scrobbles)

  duplicatas = df.duplicated(subset=["user", "uts", "artista", "faixa"]).sum()
  if duplicatas:
    print(f"Duplicatas removidas: {duplicatas}")
  df = df.drop_duplicates(subset=["user", "uts", "artista", "faixa"])

  df['data_hora'] = pd.to_numeric(df['uts'], errors='coerce')
  df['data_hora'] = pd.to_datetime(df['data_hora'], unit="s", utc=True)
  df['data_hora'] = df['data_hora'].dt.tz_convert('America/Sao_Paulo')
  df['uts'] = df['uts'].astype('int64')

  return {
    "df": df,
    "total_scrobbles": total_scrobbles,
    "paginas_com_erro_final": paginas_com_erro_final
}



# Retorna os N artistas similares de acordo com a API
def get_similar_artists(top_artistas, n):

  lista_similar_artists = []
  artistas_com_erro = []
  artistas_com_erro_final = []

  for artista_semente in top_artistas.index:
    loop_params = {
        "method": "artist.getsimilar",
        "artist": artista_semente,
        "limit": n
    }

    data = fetch_lastfm_data(API_KEY, loop_params, DEFAULT_RETRIES)

    if data:
      if data['similarartists']['artist']:
        rank_cont = 1
        for artista_similar in data['similarartists']['artist']:
          if rank_cont > n:
            break

          lista_similar_artists.append(
              {
                  "semente": artista_semente,
                  "candidato": artista_similar['name'],
                  "match_lastfm": float(artista_similar['match'])
              }
          )
          rank_cont += 1
      else:
        print(f"O artista {artista_semente} não possui similares.")
        continue
    else:
      print(f"Erro ao salvar {artista_semente}...")
      artistas_com_erro.append(artista_semente)
      continue

    print(f"OK: {artista_semente}")



  if artistas_com_erro:
    for artista_semente in artistas_com_erro:
      print(f"Testando novamente {artista_semente}")
      loop_params = {
          "method": "artist.getsimilar",
          "artist": artista_semente,
          "limit": n
      }

      data = fetch_lastfm_data(API_KEY, loop_params, DEFAULT_RETRIES)

      if data:
        if data['similarartists']['artist']:
          rank_cont = 1
          for artista_similar in data['similarartists']['artist']:
            if rank_cont > n:
              break

            lista_similar_artists.append(
                {
                    "semente": artista_semente,
                    "candidato": artista_similar['name'],
                    "match_lastfm": float(artista_similar['match'])
                }
            )
            rank_cont += 1

        else:
          print(f"O artista {artista_semente} não possui similares.")
          continue
      else:
        print(f"Erro ao salvar {artista_semente}...")
        artistas_com_erro_final.append(artista_semente)
        continue

  if artistas_com_erro_final:
    print(f"Existem artistas com erro:")
    for artista in artistas_com_erro_final:
      print(artista)

  else:
    print("Concluído com sucesso.")

  df = pd.DataFrame(lista_similar_artists)
  return df



# Busca as tags de um df de candidatos
def busca_tags_candidatos(top_candidatos):

  lista_artist_tag = []
  artist_tag_com_erro = []
  artist_tag_com_erro_final = []
  cont_art = 1
  tamanho = len(top_candidatos)

  for artista in top_candidatos:
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
      artist_tag_com_erro.append(artista)


    print(f"[{cont_art}/{tamanho}] {artista}.\n")
    cont_art += 1

  if artist_tag_com_erro:
    print("\nExistem artistas com erro! Tentando novamente...")

    for artista in artist_tag_com_erro:
      print(f"Testando novamente artista: {artista}")
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


  df_final = pd.DataFrame(lista_artist_tag)

  duplicatas = df_final.duplicated(
    subset=['artista', 'tag']
).sum()

  if duplicatas > 0:
    print(f"Duplicatas removidas: {duplicatas}")
    df_final = df_final.drop_duplicates(
        subset=['artista', 'tag']
    )

  print("Sincronização concluída.")
  return df_final