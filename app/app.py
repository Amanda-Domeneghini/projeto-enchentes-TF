import streamlit as st

# - Pra instalar e rodar:
# pip install streamlit
# streamlit run app/app.py

st.title("Dashboard de Enchentes em Porto Alegre — INCT SiMAI")
st.write("Nomes: Amanda Flores Domeneghini, Milena Fontana Bregalda, Mariana Nunes dos Santos, Karen Cristiane Nascimento")

st.sidebar.title("Navegação")
tela_selecionada = st.sidebar.radio(
    "Escolha a tela:", 
    ["Tela 1", "Tela 2"]
)

if tela_selecionada == "Tela 1":
    st.header("Tela 1")
    st.write("Conteúdo da tela 1")
    

elif tela_selecionada == "Tela 2":
    st.header("Tela 2")
    st.write("Conteúdo da tela 2.")