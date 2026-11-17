from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


st.set_page_config(page_title="Dashboard Bases Externas", layout="wide")

TURQUESA = "#009DAE"
VERDE = "#22C55E"
VERMELHO = "#EF4444"
CINZA_AZULADO = "#94A3B8"

st.markdown(
    """
    <style>
    .st-key-cartao_mapa,
    .st-key-cartao_ranking,
    .st-key-cartao_linha {
        background-color: #F9FCFC;
        border: 1px solid #CADDE1;
        border-radius: 18px;
        padding: 16px;
        box-shadow: 0 4px 14px rgba(35, 64, 74, 0.08);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def mostrar_mapa(casas, niveis):
    cotas = sorted(niveis["nivel_m"].unique())

    with st.container(key="cartao_mapa"):
        st.subheader("Casas de bombas por cota")

        cota = st.select_slider(
            "Selecione a cota",
            options=cotas,
            format_func=lambda valor: f"{valor:.1f} m".replace(".", ","),
        )

        resultados = niveis.loc[
            niveis["nivel_m"] == cota,
            ["fid", "intersecao_retornada"],
        ]

        casas_mapa = casas.merge(resultados, on="fid", how="left")
        casas_mapa["cor"] = (
            casas_mapa["intersecao_retornada"]
            .map({True: VERMELHO, False: VERDE})
            .fillna(CINZA_AZULADO)
        )

        st.caption(
            "🔴 Com interseção registrada · "
            "🟢 Sem interseção registrada · "
            "⚪ Sem dado"
        )

        st.map(
            casas_mapa,
            latitude="latitude",
            longitude="longitude",
            color="cor",
            height=440,
        )

    return cota


def mostrar_ranking_cotas(resumo):
    ranking = resumo.dropna(subset=["menor_cota_m"]).sort_values("menor_cota_m")

    grafico = (
        alt.Chart(ranking)
        .mark_bar(color=TURQUESA, cornerRadiusEnd=4)
        .encode(
            x=alt.X("menor_cota_m:Q", title="Menor cota com interseção (m)"),
            y=alt.Y(
                "nome:N",
                title=None,
                sort=ranking["nome"].tolist(),
                axis=alt.Axis(labelLimit=180),
            ),
            tooltip=[
                alt.Tooltip("nome:N", title="Casa de bombas"),
                alt.Tooltip("menor_cota_m:Q", title="Cota (m)", format=".1f"),
            ],
        )
        .properties(height=500)
    )

    with st.container(key="cartao_ranking"):
        st.subheader("Menor cota com interseção")
        st.altair_chart(grafico)


def mostrar_linha_intersecoes(niveis, cota_selecionada):
    cotas = sorted(niveis["nivel_m"].unique())

    # Conta cada casa uma vez por cota e mantém as cotas com zero interseções.
    contagem = (
        niveis.loc[niveis["intersecao_retornada"].eq(True)]
        .groupby("nivel_m")["fid"]
        .nunique()
        .reindex(cotas, fill_value=0)
        .rename_axis("nivel_m")
        .reset_index(name="total_casas")
    )

    eixo_cota = alt.X(
        "nivel_m:Q",
        title="Cota (m)",
        scale=alt.Scale(zero=False),
    )

    linha = (
        alt.Chart(contagem)
        .mark_line(color=TURQUESA, strokeWidth=3, point=True)
        .encode(
            x=eixo_cota,
            y=alt.Y(
                "total_casas:Q",
                title="Casas com interseção",
                axis=alt.Axis(tickMinStep=1),
                scale=alt.Scale(zero=True),
            ),
            tooltip=[
                alt.Tooltip("nivel_m:Q", title="Cota (m)", format=".1f"),
                alt.Tooltip("total_casas:Q", title="Casas com interseção"),
            ],
        )
    )

    marcador = (
        alt.Chart(pd.DataFrame({"nivel_m": [cota_selecionada]}))
        .mark_rule(color="#536C75", strokeWidth=2, strokeDash=[5, 4])
        .encode(x=eixo_cota)
    )

    with st.container(key="cartao_linha"):
        st.subheader("Casas com interseção por cota")
        st.caption("A linha tracejada marca a cota selecionada no mapa.")
        st.altair_chart((linha + marcador).properties(height=260))

def mostrar_matriz_intersecoes(casas, niveis):
    cotas = sorted(niveis["nivel_m"].dropna().unique())

    # Cria uma célula para cada combinação de casa e cota.
    matriz = casas[["fid", "nome"]].merge(
        pd.DataFrame({"nivel_m": cotas}),
        how="cross",
    )
    matriz = matriz.merge(
        niveis[["fid", "nivel_m", "intersecao_retornada"]],
        on=["fid", "nivel_m"],
        how="left",
    )

    status = ["Com interseção", "Sem interseção", "Sem dado"]
    matriz["status"] = (
        matriz["intersecao_retornada"]
        .map({True: status[0], False: status[1]})
        .fillna(status[2])
    )

    # Formata as cotas com vírgula e mantém a ordem numérica no eixo.
    rotulos_cotas = [f"{cota:.1f}".replace(".", ",") for cota in cotas]
    matriz["cota_rotulo"] = matriz["nivel_m"].map(dict(zip(cotas, rotulos_cotas)))

    grafico = (
        alt.Chart(matriz)
        .mark_rect(stroke="#F9FCFC", strokeWidth=1)
        .encode(
            x=alt.X(
                "cota_rotulo:O",
                title="Cota (m)",
                sort=rotulos_cotas,
                axis=alt.Axis(labelAngle=-45, labelOverlap="greedy"),
            ),
            y=alt.Y(
                "nome:N",
                title=None,
                sort="ascending",
                axis=alt.Axis(labelLimit=240),
            ),
            color=alt.Color(
                "status:N",
                scale=alt.Scale(
                    domain=status,
                    range=[VERMELHO, VERDE, CINZA_AZULADO],
                ),
                legend=alt.Legend(title=None, orient="top"),
            ),
            tooltip=[
                alt.Tooltip("nome:N", title="Casa de bombas"),
                alt.Tooltip("cota_rotulo:O", title="Cota (m)"),
                alt.Tooltip("status:N", title="Resultado"),
            ],
        )
        .properties(height=alt.Step(18))
    )

    with st.container(key="cartao_matriz"):
        st.subheader("Matriz de interseção por cota")
        st.altair_chart(grafico)

pasta_app = Path(__file__).resolve().parent
pasta_dados = pasta_app.parent / "dados" / "processados"

casas = pd.read_json(pasta_dados / "pipeline_casas_limpas.json")
niveis = pd.read_json(pasta_dados / "pipeline_casas_por_nivel.json")
resumo = pd.read_json(pasta_dados / "pipeline_cotas_resumo.json")

st.title("Dashboard Bases Externas")
st.caption(
    "Quais casas de bombas têm interseção com a área de inundação na cota selecionada?"
)

col_mapa, col_ranking = st.columns([3, 2], gap="medium")

with col_mapa:
    cota_selecionada = mostrar_mapa(casas, niveis)

with col_ranking:
    mostrar_ranking_cotas(resumo)

mostrar_linha_intersecoes(niveis, cota_selecionada)
mostrar_matriz_intersecoes(casas, niveis)