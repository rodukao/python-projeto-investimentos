import streamlit as st
import plotly.express as px
from main import GerenciadorInvestimento

st.set_page_config(
    page_title="Gerenciados de investimentos",
    layout="wide"
)

dashboard = GerenciadorInvestimento()


st.sidebar.title("Menu Principal")
pagina = st.sidebar.selectbox(
    "Escolha uma opção",
    ["Minha Carteira", "Ativos disponíveis", "Registrar Compra", "Registrar Venda"]
)

# Página carteira
if pagina == "Minha Carteira":
    with st.spinner("Carregando"):
        st.title("Minha Carteira")
        dados = dashboard.relatorio_performance()
        st.dataframe(dados, hide_index=True)

        col1, col2 = st.columns(2, gap="medium")

        with col1:
            st.header("Carteira por ativos")
            fig = px.pie(dados, values='quantidade', names='nome')
            st.plotly_chart(fig)

        with col2:
            st.header("Valorização")
            fig = px.bar(dados, x='nome', y='rentabilidade_pct')
            st.plotly_chart(fig)


# Página registrar ativo
if pagina == "Ativos disponíveis":
    st.title("Ativos disponíveis")
    st.write("Lista baixada do site infomoney. Nem todos os ativos estão atualizados.")
    with st.spinner("Carregando..."):
        ativos_disponiveis = dashboard.retorna_ativos_cadastrados()
        st.dataframe(ativos_disponiveis)
        if st.button("Atualizar ativos"):
            st.success(dashboard.atualiza_lista_ativos())
        with st.form("form_cadastro"):
            nome = st.text_input(
                "Ticker do Ativo (Ex: PETR4, BTC-USD)").upper()
            btn_cadastrar = st.form_submit_button("Salvar Ativo")
            if btn_cadastrar:
                if nome:
                    msg = dashboard.registra_ativo(nome)
                    st.success(msg)
                else:
                    st.error("Por favor, digite o nome do ativo.")

# Página comprar ativo
if pagina == "Registrar Compra":
    st.title("Registrar Compra")
    with st.spinner("Carregando"):
        ativos_disponiveis = dashboard.retorna_ativos_cadastrados()
        ativo = st.selectbox(
            "Ativos (nem todos os ativos estão atualizados e funcionam)", ativos_disponiveis)
        try:
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
        except Exception as e:
            st.error(
                "Não foi possível retornar o valor do ativo. Tente outro ativo.")

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
            quantidade_venda = st.slider("Quantidade:", 0.0, float(quantidade_disponivel),
                                         quantidade_disponivel / 2)
            valor_total = quantidade_venda * preco_ativo
            st.metric("Total da venda", valor_total)
            btn_vender = st.button("Registrar venda")
            if btn_vender:
                msg = dashboard.vender_ativo(ativo, quantidade_venda, 0)
                st.success(msg)
