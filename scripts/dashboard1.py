import json
import re
import unicodedata
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


NIVEL_MINIMO = 3.0
NIVEL_MAXIMO = 10.0
NIVEL_RECORDE = 5.35
NIVEIS = [decimos / 10 for decimos in range(30, 101)]
TURQUESA = "#009DAE"
VERMELHO = "#EF4444"
ROXO_POPULACAO = "#7055A5"
CINZA_AZULADO = "#94A3B8"
FUNDO_CARTAO = "#F9FCFC"
COR_TEXTO = "#23404A"

# Mude para True se quiser testar a tela com seis bairros fictícios.
USAR_DADOS_FICTICIOS = False
PASTA_DADOS = Path(__file__).resolve().parent.parent / "dados" / "processados"
ARQUIVO_INCT = PASTA_DADOS / "data_inctlongoelimpo.json"
ARQUIVO_BAIRROS = PASTA_DADOS / "bairros_porto_alegre.geojson"
FONTE_BAIRROS = (
    "https://gis-smamus.portoalegre.rs.gov.br/server/rest/services/"
    "HUB/hub_base_financeiro_en/MapServer/0"
)


@st.cache_data
def carregar_dados(usar_dados_ficticios: bool) -> pd.DataFrame:
    """Retorna uma linha por bairro e nível do Guaíba."""
    if not usar_dados_ficticios:
        # Para ler um CSV ou banco, substitua esta leitura por pd.read_csv()
        # ou pd.read_sql(). Mantenha as colunas abaixo e os níveis numéricos
        # de 3,0 a 10,0, com uma única linha por par (nivel_m, bairro).
        # percentage usa a escala de 0 a 100, e affected_population é uma
        # estimativa que pode ter casas decimais.
        return pd.read_json(ARQUIVO_INCT, orient="records")

    # Os nomes dos bairros são reais. As populações, os totais de prédios
    # e os parâmetros de alagamento são inventados para a demonstração.
    # Cada tupla contém bairro, população, prédios, cota inicial em décimos
    # de metro e fração máxima dos prédios afetados no exemplo.
    bairros = [
        ("Centro Histórico", 39_500, 3_600, 36, 0.72),
        ("Menino Deus", 30_000, 4_100, 44, 0.61),
        ("Sarandi", 59_000, 11_500, 32, 0.88),
        ("Farrapos", 21_000, 4_800, 30, 0.96),
        ("Cidade Baixa", 16_800, 2_450, 46, 0.69),
        ("Praia de Belas", 4_200, 1_200, 35, 0.83),
    ]

    registros = []
    for decimos in range(30, 101):
        for bairro, populacao, predios, inicio, fracao_maxima in bairros:
            # O impacto aumenta após a cota inicial e se aproxima do
            # máximo fictício do bairro no último nível.
            progresso = max(0, decimos - inicio) / (100 - inicio)
            predios_afetados = round(predios * fracao_maxima * progresso**0.8)
            proporcao = predios_afetados / predios
            registros.append(
                {
                    "nivel_m": decimos / 10,
                    "bairro": bairro,
                    "affected_buildings": predios_afetados,
                    "total_buildings": predios,
                    "percentage": 100 * proporcao,
                    "population": populacao,
                    "affected_population": populacao * proporcao,
                }
            )
    return pd.DataFrame(registros)


def formatar_inteiro(valor: float) -> str:
    return f"{valor:,.0f}".replace(",", ".")


def formatar_decimal(valor: float, casas: int = 1) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def chave_bairro(nome: str) -> str:
    texto = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    chave = re.sub(r"[^a-z0-9]", "", texto.lower())
    # O mesmo bairro tem nomes diferentes no cadastro municipal e no INCT.
    return {"aparicioborges": "coronelaparicioborges"}.get(chave, chave)


@st.cache_data
def carregar_limites() -> list:
    """Lê a camada municipal local, sem depender da internet ao abrir a tela."""
    with ARQUIVO_BAIRROS.open(encoding="utf-8") as arquivo:
        limites = json.load(arquivo)["features"]

    # O GeoJSON municipal segue a orientação RFC 7946. A projeção do Vega
    # usa a convenção D3, de orientação inversa para polígonos pequenos.
    for bairro in limites:
        geometria = bairro["geometry"]
        coordenadas = geometria["coordinates"]
        if geometria["type"] == "Polygon":
            coordenadas = [coordenadas]

        bairro["geometry"] = {
            "type": "MultiPolygon",
            "coordinates": [
                [anel[::-1] for anel in poligono] for poligono in coordenadas
            ],
        }
    return limites


def grafico_mapa(limites: list, dados_nivel: pd.DataFrame) -> alt.Chart:
    valores = dados_nivel.assign(chave=dados_nivel["bairro"].map(chave_bairro))
    consulta = valores.set_index("chave").to_dict(orient="index")
    bairros = []
    for feicao in limites:
        nome = feicao["properties"]["bairro"]
        registro = consulta.get(chave_bairro(nome))
        if registro is None:
            detalhe = {
                "bairro": nome,
                "faixa": "Sem dados",
                "percentual": "Sem dados",
                "predios": "Sem dados",
                "pessoas": "Sem dados",
            }
        else:
            percentual = registro["percentage"]
            if registro["affected_buildings"] == 0:
                faixa = "0%"
            elif percentual < 25:
                faixa = ">0 a <25%"
            elif percentual < 50:
                faixa = "25 a <50%"
            elif percentual < 75:
                faixa = "50 a <75%"
            else:
                faixa = "75 a 100%"
            detalhe = {
                "bairro": registro["bairro"],
                "faixa": faixa,
                "percentual": f"{formatar_decimal(percentual, 2)}%",
                "predios": formatar_inteiro(registro["affected_buildings"]),
                "pessoas": formatar_inteiro(registro["affected_population"]),
            }
        bairros.append({**feicao, "properties": detalhe})

    faixas = ["0%", ">0 a <25%", "25 a <50%", "50 a <75%", "75 a 100%", "Sem dados"]
    # Tons intermediários entre o fundo dos cartões e o turquesa da Tela 2.
    cores = [FUNDO_CARTAO, "#BBE4E8", "#7DCDD5", "#3EB5C2", TURQUESA, CINZA_AZULADO]
    return (
        alt.Chart(alt.Data(values=bairros))
        .mark_geoshape(stroke="#B8CACE", strokeWidth=0.6)
        .encode(
            color=alt.Color(
                "properties.faixa:N",
                legend=alt.Legend(title=None, orient="bottom", columns=3),
                scale=alt.Scale(domain=faixas, range=cores),
            ),
            tooltip=[
                alt.Tooltip("properties.bairro:N", title="Bairro"),
                alt.Tooltip("properties.percentual:N", title="Prédios afetados (%)"),
                alt.Tooltip("properties.predios:N", title="Prédios afetados"),
                alt.Tooltip("properties.pessoas:N", title="Pessoas afetadas (estimativa)"),
            ],
        )
        .project(type="mercator")
        .properties(height=330)
    )


def grafico_bairros(atingidos: pd.DataFrame) -> alt.Chart:
    dados = atingidos.assign(
        percentual=atingidos["percentage"].map(lambda x: f"{formatar_decimal(x, 2)}%"),
        predios=atingidos["affected_buildings"].map(formatar_inteiro),
    )
    return (
        alt.Chart(dados)
        .mark_bar(color=TURQUESA, cornerRadiusEnd=4, size=16)
        .encode(
            x=alt.X(
                "percentage:Q",
                title="Prédios afetados (%)",
                scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(values=[0, 25, 50, 75, 100], labelExpr="datum.value + '%'"),
            ),
            y=alt.Y(
                "bairro:N",
                title=None,
                sort=dados["bairro"].tolist(),
                axis=alt.Axis(labelLimit=205),
            ),
            tooltip=[
                alt.Tooltip("bairro:N", title="Bairro"),
                alt.Tooltip("percentual:N", title="Prédios afetados (%)"),
                alt.Tooltip("predios:N", title="Prédios afetados"),
            ],
        )
        .properties(height=max(330, len(dados) * 25))
    )


def grafico_populacao(curva: pd.DataFrame, nivel: float) -> alt.LayerChart:
    dados = curva.assign(
        cota=curva["nivel_m"].map(lambda x: f"{formatar_decimal(x)} m"),
        pessoas=curva["affected_population"].map(formatar_inteiro),
    )
    eixo_x = alt.X(
        "nivel_m:Q",
        title="Nível do Guaíba (m)",
        scale=alt.Scale(domain=[NIVEL_MINIMO, NIVEL_MAXIMO]),
        axis=alt.Axis(values=list(range(3, 11))),
    )
    eixo_y = alt.Y(
        "affected_population:Q",
        title="Pessoas afetadas (estimativa)",
        scale=alt.Scale(zero=True),
        axis=alt.Axis(format="~s", tickCount=5),
    )
    dicas = [
        alt.Tooltip("cota:N", title="Nível"),
        alt.Tooltip("pessoas:N", title="Pessoas afetadas (estimativa)"),
    ]
    base = alt.Chart(dados).encode(x=eixo_x, y=eixo_y)
    area = base.mark_area(color=ROXO_POPULACAO, opacity=0.14)
    linha = base.mark_line(color=ROXO_POPULACAO, strokeWidth=2.8, point=alt.OverlayMarkDef(size=13))
    linha = linha.encode(tooltip=dicas)
    referencia = alt.Chart(pd.DataFrame({"nivel_m": [NIVEL_RECORDE]})).encode(x=eixo_x)
    linha_recorde = referencia.mark_rule(color=VERMELHO, strokeWidth=1.8, strokeDash=[5, 4])
    rotulo = referencia.mark_text(
        text="Maio/2024 · 5,35 m",
        color=COR_TEXTO,
        align="left",
        baseline="top",
        dx=7,
        dy=6,
    ).encode(y=alt.value(0))
    ponto = (
        alt.Chart(dados.loc[dados["nivel_m"] == nivel])
        .mark_circle(size=130, color=ROXO_POPULACAO, opacity=1, stroke=FUNDO_CARTAO, strokeWidth=2)
        .encode(x=eixo_x, y=eixo_y, tooltip=dicas)
    )
    return (area + linha + linha_recorde + rotulo + ponto).properties(height=245)


def exibir_grafico(grafico, mapa: bool = False) -> None:
    grafico = (
        grafico.configure(background="transparent")
        .configure_view(stroke=None)
        .configure_axis(
            labelColor=COR_TEXTO,
            titleColor=COR_TEXTO,
            gridColor="#D8E4E6",
            tickColor="#B8CACE",
            labelFontSize=11,
            titleFontSize=12,
            labelPadding=6,
            domain=False,
        )
        .configure_legend(labelColor=COR_TEXTO, labelFontSize=11)
    )
    if mapa:
        # A camada interna conserva o GeoJSON como listas JSON no navegador.
        # O Streamlit converte dados no nível principal para uma tabela Arrow.
        with alt.data_transformers.enable("default", consolidate_datasets=False):
            spec = grafico.to_dict()
        spec["layer"] = [{campo: spec.pop(campo) for campo in ("data", "mark", "encoding")}]
        st.vega_lite_chart(spec=spec, use_container_width=True, theme=None)
    else:
        # Compatível com o Streamlit 1.45 e com as versões mais recentes.
        st.altair_chart(grafico, use_container_width=True, theme=None)


def configurar_estilo() -> None:
    st.markdown(
        """
        <style>
          .stApp { background: #DEE9EC; color: #23404A; }
          .stApp h1, .stApp h3, .stApp label p { color: #23404A; }
          .stApp a { color: #006C7A; }
          [data-testid="stHeader"] { background: transparent; }
          [data-testid="stMainBlockContainer"], .main .block-container {
            max-width: 1450px;
            padding: 3.4rem 2.5rem 2rem;
          }
          .inct-hero {
            border-radius: 18px;
            padding: 1.7rem 2rem;
            color: #23404A;
            background: #F9FCFC;
            border: 1px solid #CADDE1;
          }
          .inct-hero p { margin: .35rem 0 0; color: #425F69; }
          .inct-hero .inct-projeto {
            color: #006C7A; font-size: .76rem; letter-spacing: .09em;
            font-weight: 700; margin: 0;
          }
          .inct-hero h1 {
            color: #23404A; line-height: 1.12; margin: .45rem 0;
            padding: 0; font-size: clamp(1.75rem, 3.8vw, 2.7rem);
          }
          [data-testid="stMetric"] {
            background: #F9FCFC; border: 1px solid #CADDE1;
            border-top: 3px solid #009DAE; border-radius: 12px;
            padding: .75rem 1rem .9rem;
          }
          [data-testid="stMetricLabel"] p { color: #425F69; font-size: .9rem; }
          [data-testid="stMetricValue"] { color: #23404A; font-size: 2rem; }
          [data-testid="stVerticalBlockBorderWrapper"] {
            background: #F9FCFC; border-color: #CADDE1; border-radius: 14px;
          }
          [data-testid="stCaptionContainer"] p { color: #425F69; }
          @media (max-width: 750px) {
            [data-testid="stMainBlockContainer"], .main .block-container {
              padding-inline: .9rem;
            }
            .inct-hero { padding: 1.3rem; }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def mostrar_tela_1() -> None:
    configurar_estilo()
    st.markdown(
        """
        <div class="inct-hero">
          <p class="inct-projeto">PORTO ALEGRE · SIMULAÇÃO DO INCT SiMAI</p>
          <h1>Impactos da elevação do Guaíba</h1>
          <p>Explore a exposição de moradores e prédios conforme o nível da água sobe.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if USAR_DADOS_FICTICIOS:
        st.warning("Demonstração com dados fictícios de seis bairros.")

    with st.container(border=True):
        nivel = st.slider(
            "Nível do Guaíba",
            min_value=NIVEL_MINIMO,
            max_value=NIVEL_MAXIMO,
            value=5.3,
            step=0.1,
            format="%.1f m",
            key="nivel_tela_1",
        )
        nivel = round(nivel, 1)
        st.caption(f"Cota selecionada · {formatar_decimal(nivel)} m")

    try:
        dados = carregar_dados(USAR_DADOS_FICTICIOS)
    except (OSError, ValueError):
        st.error(f"Coloque {ARQUIVO_INCT.name} na pasta dados/processados.")
        return

    dados_nivel = dados.loc[dados["nivel_m"].round(1) == nivel]
    atingidos = dados_nivel.loc[dados_nivel["affected_buildings"] > 0].sort_values(
        ["percentage", "affected_buildings", "bairro"], ascending=[False, False, True]
    )
    curva = (
        dados.groupby("nivel_m", as_index=True)["affected_population"].sum()
        .reindex(NIVEIS).rename_axis("nivel_m").reset_index()
    )

    pessoas, predios, bairros = st.columns(3)
    pessoas.metric("Pessoas afetadas · estimativa", formatar_inteiro(dados_nivel["affected_population"].sum()))
    predios.metric("Prédios afetados", formatar_inteiro(dados_nivel["affected_buildings"].sum()))
    bairros.metric("Bairros atingidos", f"{atingidos['bairro'].nunique()} de {dados_nivel['bairro'].nunique()}")

    coluna_mapa, coluna_barras = st.columns([1.1, 1])
    with coluna_mapa, st.container(border=True):
        st.subheader("Exposição por bairro")
        st.caption("A cor indica o percentual de prédios afetados no bairro inteiro.")
        try:
            limites = carregar_limites()
        except (OSError, ValueError, KeyError):
            st.info(f"Para exibir o mapa, coloque {ARQUIVO_BAIRROS.name} na pasta dados/processados.")
        else:
            exibir_grafico(grafico_mapa(limites, dados_nivel), mapa=True)
        st.caption(f"Limites dos bairros · [Prefeitura de Porto Alegre]({FONTE_BAIRROS})")

    with coluna_barras, st.container(border=True):
        st.subheader("Prédios afetados por bairro")
        if atingidos.empty:
            st.caption("Nenhum bairro atingido nesta cota.")
        else:
            st.caption("Ordem pelo percentual de prédios afetados.")
            if len(atingidos) > 10 and st.checkbox("Mostrar todos os bairros atingidos"):
                with st.container(height=380, border=False):
                    exibir_grafico(grafico_bairros(atingidos))
            else:
                exibir_grafico(grafico_bairros(atingidos.head(10)))

    with st.container(border=True):
        st.subheader("População afetada por nível")
        cobertura = "dos seis bairros do exemplo" if USAR_DADOS_FICTICIOS else "de Porto Alegre"
        st.caption(f"Estimativa {cobertura} ao longo das cotas simuladas. O ponto marca a cota selecionada.")
        exibir_grafico(grafico_populacao(curva, nivel))

    with st.container(border=True):
        st.subheader("Ranking dos bairros atingidos")
        if atingidos.empty:
            st.caption("Nenhum bairro atingido nesta cota.")
        else:
            st.caption("Ordem inicial pelo percentual de prédios afetados.")
            ranking = atingidos[
                ["bairro", "percentage", "affected_buildings", "total_buildings", "affected_population"]
            ].copy()
            ranking["percentage"] = ranking["percentage"].round(2)
            ranking["affected_population"] = ranking["affected_population"].round().astype(int)
            ranking.insert(0, "posicao", range(1, len(ranking) + 1))
            st.dataframe(
                ranking,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "posicao": "Posição",
                    "bairro": "Bairro",
                    "percentage": st.column_config.NumberColumn(
                        "% de prédios afetados", format="%.2f"
                    ),
                    "affected_buildings": "Prédios afetados",
                    "total_buildings": "Total de prédios",
                    "affected_population": "Pessoas afetadas (estimativa)",
                },
            )

    st.info(
        "A estimativa do INCT multiplica a população de cada bairro pela proporção de prédios "
        "afetados e pressupõe distribuição uniforme entre as edificações, inclusive as não "
        "residenciais. A cor no mapa resume o bairro inteiro, sem delimitar a mancha de inundação."
    )
    if not USAR_DADOS_FICTICIOS:
        st.caption("Fonte dos indicadores e gráficos · Simulação do INCT SiMAI, base limpa do projeto.")


if __name__ == "__main__":
    st.set_page_config(page_title="Impactos da elevação do Guaíba", layout="wide")
    mostrar_tela_1()
