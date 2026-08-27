from config import (
    DB_PATH,
    N_SEMENTES,
    N_SIMILARES,
    N_CANDIDATOS,
    HALF_LIFE_DAYS,
    PESO_LASTFM,
    PESO_TAGS,
    N_RECOMENDACOES
)

from database import (
    initialize_database,
    sync_data,
    sync_artist_tags,
    contar_scrobbles
)

from cli import (
    escolher_quantidade_recomendacoes,
    deseja_explicacoes,
    mostrar_etapa,
    exibir_recomendacoes
)

from api import get_valid_user

from preprocessing import sync_normalized_tags

from recommender import gerar_recomendacoes


def main():
    conn = initialize_database()

    try:
        mostrar_etapa("LastFM Explorer")

        user = get_valid_user()
        print(f"Usuário: {user}")

        mostrar_etapa("Sincronizando histórico")
        sync_data(conn, user)

        total_scrobbles = contar_scrobbles(user, DB_PATH)

        if total_scrobbles == 0:
            print("Esse usuário não possui scrobbles para gerar recomendações.")
            return

        mostrar_etapa("Atualizando tags")
        sync_artist_tags(user, DB_PATH)
        sync_normalized_tags(DB_PATH)

        n_recomendacoes = escolher_quantidade_recomendacoes(
            N_RECOMENDACOES
        )

        mostrar_explicacoes = deseja_explicacoes()

        mostrar_etapa("Gerando recomendações")

        ranking, detalhes_sementes, detalhes_tags = gerar_recomendacoes(
            user,
            DB_PATH,
            n_sementes=N_SEMENTES,
            n_similares=N_SIMILARES,
            n_candidatos=N_CANDIDATOS,
            half_life_days=HALF_LIFE_DAYS,
            peso_lastfm=PESO_LASTFM,
            peso_tags=PESO_TAGS
        )

        mostrar_etapa("Recomendações")

        exibir_recomendacoes(
            ranking,
            detalhes_sementes,
            detalhes_tags,
            n=n_recomendacoes,
            mostrar_explicacoes=mostrar_explicacoes
        )

        print(f"\nTotal de scrobbles analisados: {total_scrobbles}")
        print("Execução concluída.")

    except ValueError as e:
        print(f"\nNão foi possível gerar recomendações: {e}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()