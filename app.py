import streamlit as st
import pandas as pd

from dashboard_ui import (
    grafico_barras,
    grafico_linha,
    grafico_evolucao_tags,
    formatar_mes_pt,
    card_recomendacao
)

from config import DEMO_USER
from demo_data import (
    carregar_recomendacoes_demo,
    carregar_sementes_demo,
    carregar_tags_demo,
    carregar_total_scrobbles,
    carregar_total_artistas,
    carregar_top_artistas,
    carregar_scrobbles_ao_longo_tempo,
    carregar_scrobbles_por_ano,
    carregar_scrobbles_por_dia_semana,
    carregar_scrobbles_por_hora,
    carregar_descobertas_recentes,
    carregar_variacao_scrobbles,
    carregar_hora_mais_ativa,
    carregar_top_albuns,
    carregar_top_faixas,
    carregar_variacao_novos_artistas,
    carregar_top_tags,
    carregar_evolucao_tags,
    carregar_scrobbles_por_periodo_dia
)



# Main
st.set_page_config(
    page_title="LastFM Explorer",
    layout="wide"
)


st.title("LastFM Explorer")

st.caption(
    f"Dashboard demonstrativo baseado em um snapshot estático do histórico de @{DEMO_USER}. "
    f"Nenhuma chamada à API é feita nesta versão pública."
)

st.divider()

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

tab_visao, tab_habitos, tab_recomendacoes = st.tabs(
    [
        "Visão geral",
        "Hábitos de escuta",
        "Recomendações"
    ]
)


with tab_visao:

    total_scrobbles = carregar_total_scrobbles()
    total_artistas = carregar_total_artistas()

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

    st.subheader("Artistas mais ouvidos")
    top_artistas = carregar_top_artistas(
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

    st.subheader("Principais características musicais")

    top_tags = carregar_top_tags(
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

    st.subheader("Evolução das características musicais")
    evolucao_tags = carregar_evolucao_tags(
        limit=5,
        dias=dias_periodo
    )

    evolucao_tags["mes_dt"] = pd.to_datetime(
        evolucao_tags["mes"] + "-01"
    )

    evolucao_tags["mes_label"] = (
        evolucao_tags["mes_dt"]
        .dt.strftime("%b/%Y")
        .apply(formatar_mes_pt)
    )

    if evolucao_tags.empty:
        st.info(
            "Não há dados suficientes para mostrar a evolução das tags."
        )
    else:
        grafico_evolucao_tags(evolucao_tags)

    st.divider()

    st.subheader("Álbuns mais ouvidos")

    top_albuns = carregar_top_albuns(
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

    st.subheader("Faixas mais ouvidas")

    top_faixas = carregar_top_faixas(
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

    st.subheader("Scrobbles ao longo do tempo")

    scrobbles_tempo = carregar_scrobbles_ao_longo_tempo(
        dias_periodo
    )

    scrobbles_tempo["periodo_dt"] = pd.to_datetime(
        scrobbles_tempo["periodo"]
    )

    if dias_periodo is not None and dias_periodo <= 90:
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

    # Métricas
    hora_pico, scrobbles_pico = carregar_hora_mais_ativa(
        dias_periodo
    )

    if dias_periodo is not None:

        atual, anterior, variacao = carregar_variacao_scrobbles(
            dias_periodo
        )

        novos_atual, novos_anterior, variacao_novos = (
            carregar_variacao_novos_artistas(
                dias_periodo
            )
        )

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                f"Scrobbles nos últimos {dias_periodo} dias",
                atual
            )

        with col2:
            st.metric(
                f"Período anterior ({dias_periodo} dias)",
                anterior
            )

        with col3:
            st.metric(
                "Variação",
                f"{variacao:.1f}%"
                if variacao is not None
                else "—"
            )

        with col4:
            st.metric(
                f"Novos artistas — {dias_periodo} dias",
                novos_atual,
                (
                    f"{variacao_novos:+.1f}% vs período anterior"
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

        total_scrobbles = carregar_total_scrobbles()
        total_artistas = carregar_total_artistas()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Scrobbles no histórico",
                f"{total_scrobbles:,}".replace(",", ".")
            )

        with col2:
            st.metric(
                "Artistas diferentes",
                f"{total_artistas:,}".replace(",", ".")
            )

        with col3:
            st.metric(
                "Hora mais ativa",
                f"{hora_pico}:00",
                f"{scrobbles_pico} scrobbles"
            )

    st.divider()

    descobertas = carregar_descobertas_recentes(
        dias_periodo
    )

    if dias_periodo is None:
        st.subheader("Histórico de descobertas")

        descobertas = descobertas.head(30)

        st.caption(
            "Mostrando as 30 descobertas mais recentes do histórico."
        )

    else:
        st.subheader(
            f"Artistas descobertos nos últimos {dias_periodo} dias"
        )

    if descobertas.empty:
        st.info(
            "Nenhum artista novo identificado nesse período."
        )

    else:
        descobertas = descobertas.rename(
            columns={
                "artista": "Artista",
                "data_descoberta": "Data da descoberta"
            }
        )

        st.dataframe(
            descobertas,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Data da descoberta": st.column_config.DateColumn(
                    "Data da descoberta",
                    format="DD/MM/YYYY"
                )
            }
        )




with tab_habitos:
    st.subheader("Quando as músicas são ouvidas?")

    dias = carregar_scrobbles_por_dia_semana(
        dias_periodo
    )

    horas = carregar_scrobbles_por_hora(
        dias_periodo
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
            dias,
            x="dia",
            y="total",
            titulo_x="Dia da semana",
            titulo_y="Total",
            sort=ordem_dias
        )

    with col2:
        st.markdown("#### Horários")
        grafico_barras(
            horas,
            x="hora",
            y="total",
            titulo_x="Hora",
            titulo_y="Total"
        )

    st.divider()

    st.subheader("Distribuição por período do dia")

    periodos_dia = carregar_scrobbles_por_periodo_dia(
        dias_periodo
    )

    periodo_mais_ativo = (
        periodos_dia
        .sort_values("total", ascending=False)
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

    ordem_periodos = [
        "Madrugada",
        "Manhã",
        "Tarde",
        "Noite"
    ]

    grafico_barras(
        periodos_dia,
        x="periodo",
        y="total",
        titulo_x="Período do dia",
        titulo_y="Total",
        sort=ordem_periodos
    )

    st.divider()

    st.subheader("Scrobbles por ano")
    anos = carregar_scrobbles_por_ano()
    grafico_barras(
        anos,
        x="ano",
        y="total",
        titulo_x="Ano",
        titulo_y="Total"
    )






with tab_recomendacoes:

    with st.expander("Como essas recomendações são geradas?"):
        st.markdown(
            """
            O modelo analisa o histórico de scrobbles e constrói um
            perfil musical usando as tags dos artistas.

            **A versão atual considera:**

            - importância das tags no perfil;
            - quantidade de scrobbles;
            - maior peso para escutas recentes;
            - artistas similares fornecidos pelo Last.fm;
            - compatibilidade das tags dos candidatos com o perfil;
            - remoção de artistas que já aparecem no histórico.

            O ranking final combina **30% do sinal de similaridade do
            Last.fm** com **70% da compatibilidade das tags**.
            """
        )

    st.subheader("Recomendações de artistas")

    st.write(
        "Artistas ainda não presentes no histórico de escuta, "
        "selecionados a partir do perfil musical e das relações "
        "entre artistas no Last.fm."
    )

    recomendacoes = carregar_recomendacoes_demo()
    sementes = carregar_sementes_demo()
    tags = carregar_tags_demo()

    for _, row in recomendacoes.iterrows():

        artista = row["artista"]
        rank = int(row["rank"])
        score = float(row["score"])

        sementes_artista = (
            sementes[
                sementes["artista"] == artista
            ]
            .sort_values(
                "contribuicao",
                ascending=False
            )
            .head(3)
        )

        tags_artista = (
            tags[
                tags["artista"] == artista
            ]
            .sort_values(
                "compatibilidade",
                ascending=False
            )
            .head(3)
        )

        card_recomendacao(
            rank,
            artista,
            score,
            sementes_artista,
            tags_artista
        )


st.divider()

st.markdown(
    """
    <div style="text-align: center; opacity: 0.7; font-size: 0.85rem;">
        Projeto acadêmico independente e não oficial.<br>
        Dados provenientes do Last.fm.<br>
        A versão pública utiliza um snapshot estático e não realiza chamadas à API.
    </div>
    """,
    unsafe_allow_html=True
)