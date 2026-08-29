import pandas as pd
import streamlit as st

from api import validar_usuario

from analytics import (
    carregar_total_scrobbles,
    carregar_total_artistas,
    carregar_top_artistas,
    carregar_top_albuns,
    carregar_top_faixas,
    carregar_top_tags,
    carregar_evolucao_tags,
    carregar_scrobbles_ao_longo_tempo,
    carregar_variacao_scrobbles,
    carregar_variacao_novos_artistas,
    carregar_hora_mais_ativa,
    carregar_descobertas_recentes,
    carregar_scrobbles_por_dia_semana,
    carregar_scrobbles_por_hora,
    carregar_scrobbles_por_ano,
    carregar_scrobbles_por_periodo_dia
)

from dashboard_ui import (
    card_recomendacao,
    grafico_barras,
    grafico_linha,
    grafico_evolucao_tags,
    formatar_mes_pt
)

from config import (
    DB_PATH,
    N_SEMENTES,
    N_SIMILARES,
    N_CANDIDATOS,
    HALF_LIFE_DAYS,
    PESO_LASTFM,
    PESO_TAGS
)

from database import (
    initialize_database,
    sync_data,
    contar_scrobbles,
    sync_artist_tags
)

from preprocessing import sync_normalized_tags

from recommender import gerar_recomendacoes



# Funções
def preparar_usuario(user):
    conn = initialize_database()

    try:
        sync_data(conn, user)

        total_scrobbles = contar_scrobbles(
            user,
            DB_PATH
        )

        if total_scrobbles == 0:
            raise ValueError(
                "Esse usuário não possui scrobbles disponíveis."
            )

        sync_artist_tags(
            user,
            DB_PATH
        )

        sync_normalized_tags(
            DB_PATH
        )

        return total_scrobbles

    finally:
        conn.close()


def gerar_resultado_local(user):
    return gerar_recomendacoes(
        user,
        DB_PATH,
        n_sementes=N_SEMENTES,
        n_similares=N_SIMILARES,
        n_candidatos=N_CANDIDATOS,
        half_life_days=HALF_LIFE_DAYS,
        peso_lastfm=PESO_LASTFM,
        peso_tags=PESO_TAGS
    )


def iniciar_analise():
    st.session_state.processando = True
    st.session_state.iniciar_analise = True
    st.session_state.erro_analise = None

    st.session_state.resultado_local = None
    st.session_state.usuario_local = None



# Main
st.set_page_config(
    page_title="LastFM Explorer",
    layout="wide"
)

st.title("LastFM Explorer")

st.caption(
    "Analise seu histórico musical e descubra novos artistas "
    "a partir da sua conta do Last.fm."
)

st.info(
    "Esta versão utiliza a API key configurada localmente no arquivo .env."
)



# Session State
if "processando" not in st.session_state:
    st.session_state.processando = False

if "iniciar_analise" not in st.session_state:
    st.session_state.iniciar_analise = False

if "resultado_local" not in st.session_state:
    st.session_state.resultado_local = None

if "usuario_local" not in st.session_state:
    st.session_state.usuario_local = None

if "erro_analise" not in st.session_state:
    st.session_state.erro_analise = None



# Entrada do usuário
user = st.text_input(
    "Usuário do Last.fm",
    placeholder="Digite seu username",
    disabled=st.session_state.processando
).strip()


st.button(
    "Analisar meu perfil",
    type="primary",
    disabled=(
        not user
        or st.session_state.processando
    ),
    on_click=iniciar_analise
)



# Processamento
if st.session_state.iniciar_analise:

    try:
        with st.status(
            "Preparando análise...",
            expanded=True
        ) as status:


            # 1. Validação
            st.write(
                "Verificando usuário no Last.fm..."
            )

            if not validar_usuario(user):
                raise ValueError(
                    f"Não foi possível localizar o usuário "
                    f"@{user} no Last.fm."
                )

            st.write(
                "Usuário encontrado."
            )



            # 2. Inicializa banco
            st.write(
                "Preparando banco de dados local..."
            )

            conn = initialize_database()
            conn.close()

            st.write(
                "Banco de dados pronto."
            )


            # 3. Verifica histórico existente
            total_local = contar_scrobbles(
                user,
                DB_PATH
            )

            if total_local > 0:

                st.write(
                    (
                        f"{total_local:,} scrobbles "
                        f"já disponíveis localmente."
                    ).replace(",", ".")
                )

                st.write(
                    "Buscando novos scrobbles..."
                )

            else:

                st.write(
                    "Primeiro acesso deste usuário."
                )

                st.info(
                    "A sincronização inicial precisa baixar "
                    "todo o histórico e as tags dos artistas. "
                    "Dependendo do tamanho da conta, isso pode "
                    "levar alguns minutos. "
                    "Acompanhe o status da sincronização pelo terminal. "
                )

                st.write(
                    "Baixando histórico completo..."
                )


            # 4. Sincronização
            total_scrobbles = preparar_usuario(
                user
            )

            st.cache_data.clear()

            st.write(
                (
                    f"{total_scrobbles:,} "
                    f"scrobbles disponíveis."
                ).replace(",", ".")
            )


            # 5. Recomendador
            st.write(
                "Construindo perfil musical..."
            )

            st.write(
                "Buscando artistas similares..."
            )

            st.write(
                "Calculando compatibilidade das tags..."
            )

            resultado = gerar_resultado_local(
                user
            )


            # 6. Salva resultado
            st.session_state.resultado_local = (
                resultado
            )

            st.session_state.usuario_local = user

            status.update(
                label="Análise concluída!",
                state="complete",
                expanded=False
            )


    except Exception as e:

        st.session_state.erro_analise = str(e)


    finally:

        st.session_state.processando = False
        st.session_state.iniciar_analise = False

        st.rerun()



# Exibição de erro
if st.session_state.erro_analise:

    st.error(
        f"ERRO: "
        f"{st.session_state.erro_analise}"
    )

if st.session_state.usuario_local is not None:

    user_atual = st.session_state.usuario_local

    periodo = st.radio(
        "Período de análise",
        [
            "Últimos 30 dias",
            "Últimos 90 dias",
            "Último ano",
            "Histórico completo"
        ],
        horizontal=True
    )

    mapa_periodos = {
        "Últimos 30 dias": 30,
        "Últimos 90 dias": 90,
        "Último ano": 365,
        "Histórico completo": None
    }

    dias_periodo = mapa_periodos[periodo]


    # Menu
    tab_visao, tab_habitos, tab_recomendacoes = st.tabs(
        [
            "Visão geral",
            "Hábitos de escuta",
            "Recomendações"
        ]
    )


    with tab_visao:

        total_scrobbles = carregar_total_scrobbles(
            user_atual,
            DB_PATH
        )

        total_artistas = carregar_total_artistas(
            user_atual,
            DB_PATH
        )

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Scrobbles analisados",
                f"{total_scrobbles:,}".replace(",", ".")
            )

        with col2:
            st.metric(
                "Artistas diferentes",
                f"{total_artistas:,}".replace(",", ".")
            )

        st.divider()

        # Top artistas
        st.subheader("Artistas mais ouvidos")

        top_artistas = carregar_top_artistas(
            user_atual,
            DB_PATH,
            limit=10,
            dias=dias_periodo
        )

        grafico_barras(
            top_artistas,
            x="artista",
            y="total",
            titulo_x="Artista",
            titulo_y="Total",
            sort="-y"
        )

        st.divider()

        # Top tags
        st.subheader(
            "Principais características musicais"
        )

        top_tags = carregar_top_tags(
            user_atual,
            DB_PATH,
            limit=10,
            dias=dias_periodo
        )

        grafico_barras(
            top_tags,
            x="tag",
            y="relevancia",
            titulo_x="Tag",
            titulo_y="Relevância",
            sort="-y"
        )

        st.divider()

        # Evolução das tags
        st.subheader(
            "Evolução das características musicais"
        )

        evolucao_tags = carregar_evolucao_tags(
            user_atual,
            DB_PATH,
            limit=5,
            dias=dias_periodo
        )

        if evolucao_tags.empty:
            st.info(
                "Não há dados suficientes para mostrar "
                "a evolução das tags."
            )

        else:
            evolucao_tags["mes_dt"] = pd.to_datetime(
                evolucao_tags["mes"] + "-01"
            )

            evolucao_tags["mes_label"] = (
                evolucao_tags["mes_dt"]
                .dt.strftime("%b/%Y")
                .apply(formatar_mes_pt)
            )

            grafico_evolucao_tags(
                evolucao_tags
            )

        st.divider()

        # Top albuns
        st.subheader("Álbuns mais ouvidos")

        top_albuns = carregar_top_albuns(
            user_atual,
            DB_PATH,
            limit=10,
            dias=dias_periodo
        )

        top_albuns["album_artista"] = (
            top_albuns["album"]
            + " — "
            + top_albuns["artista"]
        )

        grafico_barras(
            top_albuns,
            x="album_artista",
            y="total",
            titulo_x="Álbum",
            titulo_y="Total",
            sort="-x",
            horizontal=True
        )


        st.divider()

        # Top faixas
        st.subheader("Faixas mais ouvidas")

        top_faixas = carregar_top_faixas(
            user_atual,
            DB_PATH,
            limit=10,
            dias=dias_periodo
        )

        top_faixas["faixa_artista"] = (
            top_faixas["faixa"]
            + " — "
            + top_faixas["artista"]
        )

        grafico_barras(
            top_faixas,
            x="faixa_artista",
            y="total",
            titulo_x="Faixa",
            titulo_y="Total",
            sort="-x",
            horizontal=True
        )


        st.divider()

        # Scrobbles ao longo do tempo
        st.subheader(
            "Scrobbles ao longo do tempo"
        )

        scrobbles_tempo = (
            carregar_scrobbles_ao_longo_tempo(
                user_atual,
                DB_PATH,
                dias=dias_periodo
            )
        )

        scrobbles_tempo["periodo_dt"] = (
            pd.to_datetime(
                scrobbles_tempo["periodo"]
            )
        )

        if (
            dias_periodo is not None
            and dias_periodo <= 90
        ):
            scrobbles_tempo["periodo_label"] = (
                scrobbles_tempo["periodo_dt"]
                .dt.strftime("%d/%b/%Y")
                .apply(formatar_mes_pt)
            )

        else:
            scrobbles_tempo["periodo_label"] = (
                scrobbles_tempo["periodo_dt"]
                .dt.strftime("%b/%Y")
                .apply(formatar_mes_pt)
            )

        grafico_linha(
            scrobbles_tempo,
            x="periodo_label",
            y="total",
            titulo_x="Data",
            titulo_y="Total",
            campo_ordem="periodo_dt"
        )


        st.divider()

        hora_pico, scrobbles_pico = (
            carregar_hora_mais_ativa(
                user_atual,
                DB_PATH,
                dias=dias_periodo
            )
        )

        if dias_periodo is not None:

            atual, anterior, variacao = (
                carregar_variacao_scrobbles(
                    user_atual,
                    DB_PATH,
                    dias_periodo
                )
            )

            (
                novos_atual,
                novos_anterior,
                variacao_novos
            ) = carregar_variacao_novos_artistas(
                user_atual,
                DB_PATH,
                dias_periodo
            )

            col1, col2, col3, col4, col5 = (
                st.columns(5)
            )

            with col1:
                st.metric(
                    f"Scrobbles nos últimos "
                    f"{dias_periodo} dias",
                    atual
                )

            with col2:
                st.metric(
                    f"Período anterior "
                    f"({dias_periodo} dias)",
                    anterior
                )

            with col3:
                st.metric(
                    "Variação",
                    (
                        f"{variacao:.1f}%"
                        if variacao is not None
                        else "—"
                    )
                )

            with col4:
                st.metric(
                    f"Novos artistas — "
                    f"{dias_periodo} dias",
                    novos_atual,
                    (
                        f"{variacao_novos:+.1f}% "
                        f"vs período anterior"
                        if variacao_novos is not None
                        else None
                    )
                )

            with col5:
                st.metric(
                    "Hora mais ativa",
                    f"{hora_pico}:00",
                    f"{scrobbles_pico} scrobbles"
                )

        else:

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Scrobbles no histórico",
                    f"{total_scrobbles:,}"
                    .replace(",", ".")
                )

            with col2:
                st.metric(
                    "Artistas diferentes",
                    f"{total_artistas:,}"
                    .replace(",", ".")
                )

            with col3:
                st.metric(
                    "Hora mais ativa",
                    f"{hora_pico}:00",
                    f"{scrobbles_pico} scrobbles"
                )


        st.divider()

        # Descobertas
        descobertas = carregar_descobertas_recentes(
            user_atual,
            DB_PATH,
            dias=dias_periodo
        )

        if dias_periodo is None:

            st.subheader(
                "Histórico de descobertas"
            )

            descobertas = descobertas.head(30)

            st.caption(
                "Mostrando as 30 descobertas "
                "mais recentes do histórico."
            )

        else:

            st.subheader(
                f"Artistas descobertos nos últimos "
                f"{dias_periodo} dias"
            )

        if descobertas.empty:

            st.info(
                "Nenhum artista novo identificado "
                "nesse período."
            )

        else:

            descobertas = descobertas.rename(
                columns={
                    "artista": "Artista",
                    "data_descoberta":
                        "Data da descoberta"
                }
            )

            st.dataframe(
                descobertas,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Data da descoberta":
                        st.column_config.DateColumn(
                            "Data da descoberta",
                            format="DD/MM/YYYY"
                        )
                }
            )

    with tab_habitos:

        st.subheader("Scrobbles por dia da semana")

        dias_semana = carregar_scrobbles_por_dia_semana(
            user_atual,
            DB_PATH,
            dias=dias_periodo
        )

        por_hora = carregar_scrobbles_por_hora(
            user_atual,
            DB_PATH,
            dias=dias_periodo
        )

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Dias da semana")

            ordem_dias = [
                "Domingo",
                "Segunda",
                "Terça",
                "Quarta",
                "Quinta",
                "Sexta",
                "Sábado"
            ]

            grafico_barras(
                dias_semana,
                x="dia",
                y="total",
                titulo_x="Dia da semana",
                titulo_y="Scrobbles",
                sort=ordem_dias,
            )


        with col2:
            st.markdown("#### Horários")

            grafico_barras(
                por_hora,
                x="hora",
                y="total",
                titulo_x="Hora",
                titulo_y="Scrobbles"
            )

        st.divider()

        st.subheader("Distribuição por período do dia")

        periodos_dia = carregar_scrobbles_por_periodo_dia(
            user_atual,
            DB_PATH,
            dias=dias_periodo
        )

        ordem_periodos = [
            "Madrugada",
            "Manhã",
            "Tarde",
            "Noite"
        ]

        periodos_dia["periodo"] = pd.Categorical(
            periodos_dia["periodo"],
            categories=ordem_periodos,
            ordered=True
        )

        periodos_dia = (
            periodos_dia
            .sort_values("periodo")
        )

        grafico_barras(
            periodos_dia,
            x="periodo",
            y="total",
            titulo_x="Período",
            titulo_y="Scrobbles"
        )


        if not periodos_dia.empty:

            periodo_mais_ativo = (
                periodos_dia
                .sort_values(
                    "total",
                    ascending=False
                )
                .iloc[0]
            )

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Período mais ativo",
                    periodo_mais_ativo["periodo"]
                )

            with col2:
                st.metric(
                    "Scrobbles nesse período",
                    int(periodo_mais_ativo["total"])
                )


        st.divider()

        st.subheader(
            "Scrobbles por ano"
        )

        st.caption(
            "Esta visualização sempre considera "
            "todo o histórico disponível."
        )

        por_ano = carregar_scrobbles_por_ano(
            user_atual,
            DB_PATH
        )

        grafico_barras(
            por_ano,
            x="ano",
            y="total",
            titulo_x="Ano",
            titulo_y="Scrobbles"
        )



    with tab_recomendacoes:

        st.subheader(
            f"Recomendações para @{user_atual}"
        )

        with st.expander(
            "Como essas recomendações são geradas?"
        ):
            st.markdown(
                """
                As recomendações combinam diferentes sinais
                do seu histórico musical:

                - importância das tags dos artistas;
                - quantidade de reproduções;
                - peso maior para escutas mais recentes;
                - artistas similares fornecidos pelo Last.fm;
                - compatibilidade entre as tags dos candidatos
                  e o seu perfil musical;
                - remoção de artistas que você já ouviu.

                O score final combina:

                - **30% similaridade do Last.fm**
                - **70% compatibilidade das tags**

                O valor exibido é um score de ranking,
                não uma probabilidade.
                """
            )

        if st.session_state.resultado_local is None:

            st.info(
                "Nenhuma recomendação foi gerada ainda."
            )

        else:

            ranking, detalhes_sementes, detalhes_tags = (
                st.session_state.resultado_local
            )

            for rank, artista in enumerate(
                ranking.head(10).index,
                start=1
            ):

                score = float(
                    ranking.loc[
                        artista,
                        "score_recomendacao"
                    ]
                )


                sementes_artista = (
                    detalhes_sementes[
                        detalhes_sementes["candidato"]
                        == artista
                    ]
                    .sort_values(
                        "contribuicao",
                        ascending=False
                    )
                    .head(3)
                )


                tags_artista = (
                    detalhes_tags[
                        detalhes_tags["artista"]
                        == artista
                    ]
                    .sort_values(
                        "compatibilidade_tag",
                        ascending=False
                    )
                    .head(3)
                    .rename(
                        columns={
                            "compatibilidade_tag":
                                "compatibilidade"
                        }
                    )
                )


                card_recomendacao(
                    rank,
                    artista,
                    score,
                    sementes_artista,
                    tags_artista
                )