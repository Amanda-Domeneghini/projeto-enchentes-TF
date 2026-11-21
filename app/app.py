import streamlit as st

# - Pra instalar e rodar:
# pip install streamlit
# streamlit run app/app.py

scripts = Path(__file__).resolve().parent.parent / "scripts"
pagina = st.navigation(
    [
        st.Page(scripts / "dashboard1.py", title="Tela 1 · Impactos da enchente", default=True),
        st.Page(scripts / "dashboard2.py", title="Tela 2 · Casas de bomba", url_path="dashboard2"),
    ],
    expanded=True,
)
pagina.run()

st.sidebar.caption(
    "Equipe\n\nAmanda Flores Domeneghini · Milena Fontana Bregalda · "
    "Mariana Nunes dos Santos · Karen Cristiane Nascimento"
)