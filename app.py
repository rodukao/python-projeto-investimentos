import streamlit as st
from main import GerenciadorInvestimento

st.set_page_config(
    page_title="Gerenciados de investimentos",
    layout="wide"
)

dashboard = GerenciadorInvestimento()


st.sidebar.title("Menu Principal")
pagina = st.sidebar.selectbox(
    "Escolha uma opção", 
    ["Minha Carteira", "Cadastrar Ativo", "Registrar Compra", "Registrar Venda"]
)

if pagina == "Minha Carteira":
    with st.spinner("Carregando"):
         st.title("Carteira")
         dados = dashboard.relatorio_performance()
         st.dataframe(dados)

# --- PÁGINA: CADASTRAR ATIVO ---
if pagina == "Cadastrar Ativo":
    st.title("Cadastrar Novo Ativo")
    with st.form("form_cadastro"):
        nome = st.text_input("Ticker do Ativo (Ex: PETR4, BTC-USD)").upper()
        tipo = st.selectbox("Tipo de Ativo", ["Ação", "Fundo Imobiliário", "Cripto"])
        btn_cadastrar = st.form_submit_button("Salvar Ativo")
        
        if btn_cadastrar:
            if nome:
                # Aqui pegamos o retorno da função que você deve ajustar no main.py
                msg = dashboard.registra_ativo(nome, tipo)
                st.success(msg)
            else:
                st.error("Por favor, digite o nome do ativo.")
    
# if submit:
#     msg = dashboard.registra_ativo(nome_ativo, tipo_ativo)
#     st.success(msg)

# if st.sidebar.button("Registrar compra"):
#     print("Oi")

# if st.sidebar.button("Registrar venda"):
#     st.write("")