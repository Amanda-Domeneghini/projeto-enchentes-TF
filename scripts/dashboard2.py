from html import escape
from pathlib import Path
from typing import Literal

import altair as alt
import pandas as pd
import streamlit as st

# python -m streamlit run scripts/dashboard2.py^C

st.set_page_config(page_title="Dashboard Bases Externas", layout="wide")

TURQUESA = "#009DAE"
VERDE = "#22C55E"
VERMELHO = "#EF4444"
CINZA_AZULADO = "#94A3B8"
ALTURA_CARTAO = 425
COTA_MAIO_2024 = 5.35
PORTAL_GIS = "https://gis-smamus.portoalegre.rs.gov.br/server/rest/services"

st.markdown(
    """
    <style>
    .stApp {background:#DEE9EC;color:#23404A;}
    [data-testid="stMainBlockContainer"] {max-width:1680px;padding:3rem 2rem 1rem;}
    [class*="st-key-cartao_"] {background:#F9FCFC;border:1px solid #CADDE1;
        border-radius:16px;padding:12px 16px;gap:.35rem;box-sizing:border-box;}
    .stApp h1,.stApp h3,.stApp label p {color:#23404A;}
    .st-key-cabecalho {text-align:center;gap:.2rem;}
    .st-key-cabecalho h1 {justify-content:center;}
    .st-key-controle_nivel {background:#F9FCFC;border:1px solid #CADDE1;border-radius:16px;padding:10px 22px;}
    .stApp h1 {font-size:clamp(1.65rem,2.8vw,2.6rem);}
    [class*="st-key-cartao_"] .cabecalho-grafico {padding:0 0 8px;}
    [class*="st-key-cartao_"] .cabecalho-grafico h3 {
        margin:0;padding:0;font-size:1.05rem;line-height:1.4;}
    .cabecalho-grafico p {margin:5px 0 0;color:#425F69;font-size:.76rem;line-height:1.5;}
    [class*="st-key-cartao_"] [data-testid="stElementContainer"]:has(.cabecalho-grafico) {
        flex:0 0 auto;min-height:max-content;}

    .stApp [data-testid="stCaptionContainer"] p {font-size:.76rem;color:#425F69;line-height:1.4;}
    .stApp a {color:#006C7A;}
    @media(max-width:850px){[data-testid="stMainBlockContainer"]{padding-inline:1rem;}}
    </style>
    """,
    unsafe_allow_html=True,
)


def cabecalho_cartao(titulo, legenda=""):
    descricao = f"<p>{escape(legenda)}</p>" if legenda else ""
    st.html(f'<div class="cabecalho-grafico"><h3>{escape(titulo)}</h3>{descricao}</div>')


def exibir_grafico(grafico, altura: Literal["stretch", "content"] = "stretch"):
    grafico = (grafico.configure(background="transparent")
                .configure_view(stroke=None)
                .configure_axis(labelColor="#23404A", titleColor="#23404A",
                                gridColor="#D8E4E6", domain=False, tickColor="#B8CACE")
                .configure_legend(labelColor="#23404A", titleColor="#23404A"))
    if altura == "stretch":
        grafico = grafico.properties(height=300)
    st.altair_chart(grafico, theme=None, use_container_width=True)


def mostrar_mapa(casas, niveis, cota):

    with st.container(key="cartao_mapa", height=ALTURA_CARTAO):
        cabecalho_cartao('Localização das casas de bomba', 'Vermelho · com interseção\u3000 Verde · sem interseção\u3000 Cinza · sem dado')

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

        st.map(
            casas_mapa,
            latitude="latitude",
            longitude="longitude",
            color="cor",
            height=270,
        )
        mostrar_fontes()



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
                alt.Tooltip("menor_cota_m:Q", title="Cota (m)", format=".2f"),
            ],
        )
    )

    with st.container(key="cartao_ranking", height=ALTURA_CARTAO):
        cabecalho_cartao('Menor cota com interseção')
        exibir_grafico(grafico)
        mostrar_fontes()


def contar_intersecoes_por_cota(niveis):
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

    return contagem


def mostrar_linha_intersecoes(contagem, cota_selecionada):
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
                alt.Tooltip("nivel_m:Q", title="Cota (m)", format=".2f"),
                alt.Tooltip("total_casas:Q", title="Casas com interseção"),
            ],
        )
    )

    marcador = (
        alt.Chart(pd.DataFrame({"nivel_m": [cota_selecionada]}))
        .mark_rule(color="#536C75", strokeWidth=2, strokeDash=[5, 4])
        .encode(x=eixo_cota)
    )

    with st.container(key="cartao_linha", height=ALTURA_CARTAO):
        cabecalho_cartao('Casas com interseção por cota', 'A linha tracejada marca a cota selecionada no filtro.')
        exibir_grafico(linha + marcador)
        mostrar_fontes()

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
    rotulos_cotas = [f"{cota:.2f}".replace(".", ",") for cota in cotas]
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
    )

    with st.container(key="cartao_matriz", height=ALTURA_CARTAO):
        cabecalho_cartao('Matriz de interseção por cota')
        exibir_grafico(grafico)
        mostrar_fontes()

def mostrar_comparacao_inct(contagem, simulacao, cota_selecionada):
    # Cada linha do INCT representa um bairro em uma cota.
    populacao = (
        simulacao.groupby("nivel_m", as_index=False)["affected_population"]
        .sum(min_count=1)
        .rename(columns={"affected_population": "pessoas_afetadas"})
    )
    cota_minima = contagem["nivel_m"].min()
    cota_maxima = contagem["nivel_m"].max()
    populacao = populacao[populacao["nivel_m"].between(cota_minima, cota_maxima)]

    if populacao.empty:
        st.warning("A simulação do INCT não possui dados na faixa de cotas municipais.")
        return

    eixo_cota = alt.X(
        "nivel_m:Q",
        title="Nível do Guaíba (m)",
        scale=alt.Scale(domain=[cota_minima - 0.05, cota_maxima + 0.05], nice=False),
    )
    referencia = (
        alt.Chart(pd.DataFrame({"nivel_m": [COTA_MAIO_2024]}))
        .mark_rule(color=VERMELHO, strokeWidth=2, strokeDash=[5, 4])
        .encode(x=eixo_cota)
    )
    selecionada = (
        alt.Chart(pd.DataFrame({"nivel_m": [cota_selecionada]}))
        .mark_rule(color="#536C75", strokeWidth=2)
        .encode(x=eixo_cota)
    )
    casas = (
        alt.Chart(contagem)
        .mark_point(color=TURQUESA, filled=True, size=65)
        .encode(
            x=eixo_cota,
            y=alt.Y("total_casas:Q", title="Casas com interseção",
                    axis=alt.Axis(tickMinStep=1)),
            tooltip=[
                alt.Tooltip("nivel_m:Q", title="Cota (m)", format=".2f"),
                alt.Tooltip("total_casas:Q", title="Casas com interseção"),
            ],
        )
    )
    pessoas = (
        alt.Chart(populacao)
        .mark_line(color="#7055A5", point=True)
        .encode(
            x=eixo_cota,
            y=alt.Y("pessoas_afetadas:Q", title="Pessoas afetadas (estimativa)"),
            tooltip=[
                alt.Tooltip("nivel_m:Q", title="Cota (m)", format=".2f"),
                alt.Tooltip("pessoas_afetadas:Q", title="Pessoas afetadas", format=".0f"),
            ],
        )
    )

    with st.container(key="cartao_comparacao", height=ALTURA_CARTAO):
        cabecalho_cartao('Exposição das casas e população afetada', 'Linha cinza · cota selecionada. Tracejado vermelho · recorde de maio de 2024 (5,35 m).')
        grafico = alt.vconcat(
            (selecionada + referencia + casas).properties(height=102),
            (selecionada + referencia + pessoas).properties(height=102),
        ).resolve_scale(x="shared")
        exibir_grafico(grafico, altura="content")
        mostrar_fontes(incluir_inct=True)



def mostrar_fontes(incluir_inct=False):
    fontes = (
        f"[Casas de Bomba (EBAP)]({PORTAL_GIS}/Hosted/Casas_de_Bomba___EBAP_210126/FeatureServer/0)"
        f" · [Cotas de inundação]({PORTAL_GIS}/01_PUBLICACOES/cotas_inundacao_300_535/FeatureServer/0)"
    )
    if incluir_inct:
        fontes += " · [INCT SiMAI](https://inct-simai.com.br/?lang=pt_BR)"
    st.caption("Fontes · " + fontes)




pasta_app = Path(__file__).resolve().parent
pasta_dados = pasta_app.parent / "dados" / "processados"

casas = pd.read_json(pasta_dados / "pipeline_casas_limpas.json")
niveis = pd.read_json(pasta_dados / "pipeline_casas_por_nivel.json")
resumo = pd.read_json(pasta_dados / "pipeline_cotas_resumo.json")

with st.container(key="cabecalho"):
    st.markdown("<h1 style='text-align:center'>Casas de bomba e inundação</h1>"
                "<p style='text-align:center;margin:0'>Exposição das estações de bombeamento "
                "de Porto Alegre por nível do Guaíba</p>", unsafe_allow_html=True)

with st.container(key="controle_nivel"):
    cota_selecionada = st.select_slider(
        "Nível do Guaíba",
        options=sorted(niveis["nivel_m"].unique()),
        format_func=lambda valor: f"{valor:.2f} m".replace(".", ","),
    )

contagem = contar_intersecoes_por_cota(niveis)
simulacao = pd.read_json(pasta_dados / "data_inctlongoelimpo.json")

mapa, evolucao = st.columns(2, gap="small")
with mapa:
    mostrar_mapa(casas, niveis, cota_selecionada)
with evolucao:
    mostrar_linha_intersecoes(contagem, cota_selecionada)

ranking, matriz, comparacao = st.columns(3, gap="small")
with ranking:
    mostrar_ranking_cotas(resumo)
with matriz:
    mostrar_matriz_intersecoes(casas, niveis)
with comparacao:
    mostrar_comparacao_inct(contagem, simulacao, cota_selecionada)

st.caption("Bases municipais consultadas em 27/10/2026. Datas de coleta sem confirmação. "
            "A simulação do INCT chega a 5,30 m na faixa comparada. "
            "A interseção indica possível exposição da instalação.")
