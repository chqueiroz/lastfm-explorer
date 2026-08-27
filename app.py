import streamlit as st
import altair as alt

from config import DEMO_USER
from demo_data import (
    carregar_recomendacoes_demo,
    carregar_sementes_demo,
    carregar_tags_demo,
    carregar_total_scrobbles,
    carregar_total_artistas,
    carregar_top_artistas,
    carregar_scrobbles_por_mes,
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
    carregar_evolucao_tags
)

def grafico_barras(
    df,
    x,
    y,
    titulo_x,
    titulo_y,
    sort=None,
    horizontal=False
):
    if horizontal:
        chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X(
                    y,
                    title=titulo_y
                ),
                y=alt.Y(
                    x,
                    title=None,
                    sort=sort,
                    axis=alt.Axis(labelLimit=300)
                ),
                tooltip=[
                    alt.Tooltip(x, title=titulo_x),
                    alt.Tooltip(y, title=titulo_y)
                ]
            )
            .interactive()
        )
    else:
        chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X(
                    x,
                    title=titulo_x,
                    sort=sort,
                    axis=alt.Axis(labelAngle=0)
                ),
                y=alt.Y(
                    y,
                    title=titulo_y
                ),
                tooltip=[
                    alt.Tooltip(x, title=titulo_x),
                    alt.Tooltip(y, title=titulo_y)
                ]
            )
            .interactive()
        )

    st.altair_chart(
        chart,
        use_container_width=True
    )


def grafico_linha(df, x, y, titulo_x, titulo_y):
    chart = (
        alt.Chart(df)
        .mark_line()
        .encode(
            x=alt.X(
                x,
                title=titulo_x,
                axis=alt.Axis(labelAngle=0)
            ),
            y=alt.Y(
                y,
                title=titulo_y
            ),
            tooltip=[
                alt.Tooltip(x, title=titulo_x),
                alt.Tooltip(y, title=titulo_y)
            ]
        )
        .interactive()
    )

    st.altair_chart(
        chart,
        use_container_width=True
    )


def grafico_evolucao_tags(df):
    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X(
                "mes:N",
                title="Data",
                axis=alt.Axis(labelAngle=0)
            ),
            y=alt.Y(
                "relevancia:Q",
                title="Relevância"
            ),
            color=alt.Color(
                "tag:N",
                title="Tag"
            ),
            tooltip=[
                alt.Tooltip("mes:N", title="Mês"),
                alt.Tooltip("tag:N", title="Tag"),
                alt.Tooltip(
                    "relevancia:Q",
                    title="Relevância",
                    format=".1f"
                )
            ]
        )
        .interactive()
    )

    st.altair_chart(
        chart,
        use_container_width=True
    )


# Main
st.set_page_config(
    page_title="LastFM Explorer",
    layout="wide"
)


st.title("LastFM Explorer")

st.caption(
    f"Dashboard demonstrativo baseado no histórico real do usuário "
    f"@{DEMO_USER} no Last.fm."
)


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
    scrobbles_mes = carregar_scrobbles_por_mes()
    grafico_linha(
        scrobbles_mes,
        x="mes",
        y="total",
        titulo_x="Data",
        titulo_y="Total"
    )

    st.divider()

    atual, anterior, variacao = carregar_variacao_scrobbles(30)
    hora_pico, scrobbles_pico = carregar_hora_mais_ativa()

    novos_atual, novos_anterior, variacao_novos = (
        carregar_variacao_novos_artistas(30)
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Scrobbles nos últimos 30 dias",
            atual
        )

    with col2:
        st.metric(
            "Período anterior",
            anterior
        )

    with col3:
        st.metric(
            "Variação",
            f"{variacao:.1f}%" if variacao is not None else "—"
        )

    with col4:
        st.metric(
            "Novos artistas — 30 dias",
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

    st.divider()

    st.subheader("Descobertas recentes")
    descobertas = carregar_descobertas_recentes(30)
    if descobertas.empty:
        st.info(
            "Nenhum artista novo identificado nos últimos 30 dias."
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
            use_container_width=True
        )




with tab_habitos:
    st.subheader("Quando as músicas são ouvidas?")

    dias = carregar_scrobbles_por_dia_semana()
    horas = carregar_scrobbles_por_hora()

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
    st.subheader("Recomendações de artistas")

    st.write(
        "Artistas recomendados pelo modelo atual com base no "
        "histórico de escuta, recência, tags e similaridade do Last.fm."
    )

    recomendacoes = carregar_recomendacoes_demo()
    sementes = carregar_sementes_demo()
    tags = carregar_tags_demo()

    for _, row in recomendacoes.iterrows():

        artista = row["artista"]
        rank = int(row["rank"])
        score = row["score"]

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

        with st.container(border=True):
            st.markdown(
                f"### {rank}. {artista}"
            )

            st.caption(
                f"Score de recomendação: {score:.3f}"
            )
            if not sementes_artista.empty:
                lista_sementes = ", ".join(
                    sementes_artista["semente"].tolist()
                )

                st.write(
                    f"**Similaridade com:** {lista_sementes}"
                )
            if not tags_artista.empty:
                lista_tags = " • ".join(
                    tags_artista["tag"].tolist()
                )

                st.write(
                    f"**Características compatíveis:** {lista_tags}"
                )