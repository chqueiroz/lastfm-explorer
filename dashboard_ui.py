import altair as alt
import streamlit as st

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


def grafico_linha(
    df,
    x,
    y,
    titulo_x,
    titulo_y,
    campo_ordem=None
):
    if campo_ordem:
        sort = alt.SortField(
            field=campo_ordem,
            order="ascending"
        )
    else:
        sort = None

    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X(
                f"{x}:N",
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


def grafico_evolucao_tags(df):
    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X(
                "mes_label:N",
                title="Data",
                sort=alt.SortField(
                    field="mes_dt",
                    order="ascending"
                ),
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
                alt.Tooltip(
                    "mes_label:N",
                    title="Data"
                ),
                alt.Tooltip(
                    "tag:N",
                    title="Tag"
                ),
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


def formatar_mes_pt(data):
    meses = {
        "Jan": "jan",
        "Feb": "fev",
        "Mar": "mar",
        "Apr": "abr",
        "May": "mai",
        "Jun": "jun",
        "Jul": "jul",
        "Aug": "ago",
        "Sep": "set",
        "Oct": "out",
        "Nov": "nov",
        "Dec": "dez"
    }

    for en, pt in meses.items():
        data = data.replace(en, pt)

    return data


def card_recomendacao(
    rank,
    artista,
    score,
    sementes_artista,
    tags_artista
):
    with st.container(border=True):

        col1, col2 = st.columns(
            [4, 1],
            vertical_alignment="center"
        )

        with col1:
            st.markdown(
                f"### {rank}. {artista}"
            )

        with col2:
            st.metric(
                "Score",
                f"{score * 100:.1f}"
            )

        st.progress(float(score))

        if not sementes_artista.empty:
            lista_sementes = ", ".join(
                sementes_artista["semente"].tolist()
            )

            st.markdown(
                f"**Relacionado ao seu perfil por:** "
                f"{lista_sementes}"
            )

        if not tags_artista.empty:
            lista_tags = " · ".join(
                f"`{tag}`"
                for tag in tags_artista["tag"].tolist()
            )

            st.markdown(
                f"**Características compatíveis:** "
                f"{lista_tags}"
            )

        with st.expander("Ver detalhes técnicos"):

            if not sementes_artista.empty:
                st.markdown("**Contribuição das sementes**")

                sementes_exibir = (
                    sementes_artista[
                        [
                            "semente",
                            "match_lastfm",
                            "contribuicao"
                        ]
                    ]
                    .rename(
                        columns={
                            "semente": "Artista semente",
                            "match_lastfm": "Similaridade Last.fm",
                            "contribuicao": "Contribuição"
                        }
                    )
                )

                st.dataframe(
                    sementes_exibir,
                    hide_index=True,
                    use_container_width=True
                )

            if not tags_artista.empty:
                st.markdown("**Compatibilidade das tags**")

                tags_exibir = (
                    tags_artista[
                        [
                            "tag",
                            "compatibilidade"
                        ]
                    ]
                    .rename(
                        columns={
                            "tag": "Tag",
                            "compatibilidade": "Compatibilidade"
                        }
                    )
                )

                st.dataframe(
                    tags_exibir,
                    hide_index=True,
                    use_container_width=True
                )