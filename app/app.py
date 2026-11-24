
import streamlit as st
from pathlib import Path

# Para rodar localmente:
# streamlit run app/app.py

# Link do dashboard publicado:
# https://projeto-enchentes-tf-5p9zgebetvruspngnhm2ev.streamlit.app/

st.set_page_config(
    page_title="Dashboard de Enchentes de Porto Alegre",
    layout="wide"
)

st.markdown(
    """
    <style>
        [data-testid="stHeader"] {
            background-color: #DEE9EC;
        }

        [data-testid="stAppViewContainer"] [data-testid="stHeader"] {
            background-color: #DEE9EC;
        }
    </style>
    """,
    unsafe_allow_html=True
)

pasta_app = Path(__file__).resolve().parent

pagina = st.navigation(
    [
        st.Page(
            pasta_app / "dashboard1.py",
            title="Tela 1 - Impactos da elevação do Guaíba",
            default=True
        ),
        st.Page(
            pasta_app / "dashboard2.py",
            title="Tela 2 - Casas de bomba e inundação",
            url_path="dashboard2"
        ),
    ],
    position="top"
)

pagina.run()
