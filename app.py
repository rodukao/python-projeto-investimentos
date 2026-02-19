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

# Página carteira
if pagina == "Minha Carteira":
    with st.spinner("Carregando"):
        st.title("Carteira")
        dados = dashboard.relatorio_performance()
        st.dataframe(dados)

# Página registrar ativo
if pagina == "Cadastrar Ativo":
    st.title("Cadastrar Novo Ativo")
    with st.form("form_cadastro"):
        nome = st.text_input("Ticker do Ativo (Ex: PETR4, BTC-USD)").upper()
        tipo = st.selectbox(
            "Tipo de Ativo", ["Ação", "Fundo Imobiliário", "Cripto"])
        btn_cadastrar = st.form_submit_button("Salvar Ativo")

        if btn_cadastrar:
            if nome:
                # Aqui pegamos o retorno da função que você deve ajustar no main.py
                msg = dashboard.registra_ativo(nome, tipo)
                st.success(msg)
            else:
                st.error("Por favor, digite o nome do ativo.")

# Página comprar ativo
if pagina == "Registrar Compra":
    st.title("Registrar Compra")
    with st.spinner("Carregando"):
        ativos_disponiveis = dashboard.retorna_ativos_cadastrados()
        ativo = st.selectbox(
            "Ativos", ativos_disponiveis)
        preco_ativo = dashboard.retorna_preco_ativo(ativo)
        st.header(ativo)
        st.metric(label="BRL", value=preco_ativo)
        quantidade = st.number_input("Quantidade")
        st.header("Total")
        st.metric(label="BRL", value=preco_ativo * quantidade)
        btn_comprar = st.button("Registrar compra")
        if btn_comprar:
            if quantidade > 0:
                msg = dashboard.comprar_ativo(ativo, quantidade, 0)
                st.success(msg)
            else:
                st.error("A quantidade deve ser maior do que 0")
