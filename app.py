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

# Página venda ativo
if pagina == "Registrar Venda":
    st.title("Registrar Venda")
    with st.spinner("Carregando"):
        extrato = dashboard.extrato_consolidado()
        ativo = st.selectbox(
            "Ativos", extrato['nome'])
        if ativo:
            preco_ativo = dashboard.retorna_preco_ativo(ativo)
            st.metric(label="BRL", value=preco_ativo)
            filtro = extrato["nome"] == ativo
            quantidade_disponivel = extrato.loc[filtro, 'quantidade'].values[0]
            st.metric("quantidade disponível",
                      f"{quantidade_disponivel}")
            quantidade_venda = st.slider("Quantidade:", 0.0, quantidade_disponivel,
                                         quantidade_disponivel / 2)
            valor_total = quantidade_venda * preco_ativo
            st.metric("Total da venda", valor_total)
            btn_vender = st.button("Registrar venda")
            if btn_vender:
                msg = dashboard.vender_ativo(ativo, quantidade_venda, 0)
                st.success(msg)
