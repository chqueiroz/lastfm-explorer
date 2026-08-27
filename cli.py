from recommender import explicar_recomendacao

# Escolher quantas recomendações
def escolher_quantidade_recomendacoes(default=10):
    entrada = input(
        f"Quantas recomendações deseja receber? "
        f"[Enter = {default}]: "
    ).strip()

    if not entrada:
        return default

    try:
        quantidade = int(entrada)

        if quantidade <= 0:
            raise ValueError

        return quantidade

    except ValueError:
        print(f"Valor inválido. Usando {default}.")
        return default

# Deseja explicações
def deseja_explicacoes():
    resposta = input(
        "Deseja ver o motivo de cada recomendação? [S/N]: "
    ).strip().lower()

    return resposta in ("", "s", "sim")


# Mostrar etapa
def mostrar_etapa(mensagem):
    print(f"\n{'=' * 50}")
    print(mensagem)
    print(f"{'=' * 50}")



# Exibir recomendações
def exibir_recomendacoes(
    ranking,
    detalhes_sementes,
    detalhes_tags,
    n=10,
    mostrar_explicacoes=True
):
    print("\nRecomendações:\n")

    for rank, artista in enumerate(
        ranking.head(n).index,
        start=1
    ):
        print(f"{rank}. {artista}")

        if mostrar_explicacoes:
            explicacao = explicar_recomendacao(
                artista,
                detalhes_sementes,
                detalhes_tags
            )

            if explicacao['sementes']:
                print(
                    "   Similaridade com: "
                    + ", ".join(explicacao['sementes'])
                )

            if explicacao['tags']:
                print(
                    "   Características compatíveis: "
                    + ", ".join(explicacao['tags'])
                )

        print()