import pandas as pd
import os
import sqlite3
import yfinance as yf

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

uc.Chrome.__del__ = lambda self: None
options = uc.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = uc.Chrome(options=options, version_main=144)

url = "https://www.infomoney.com.br/cotacoes/empresas-b3/"
ativos = []


class GerenciadorInvestimento:
    def __init__(self):
        self.cria_diretorio_bd()
        self.conexao = sqlite3.connect("data/dados.db")
        self.conecta_banco()

    def cria_diretorio_bd(self):
        diretorio_projeto = os.path.abspath(os.path.curdir)
        if not os.path.exists(f"{diretorio_projeto}/data"):
            os.makedirs("data")
            print("Diretório criado com sucesso.")
        else:
            print("O diretório 'data' já existe.")

    def conecta_banco(self):
        cursor = self.conexao.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS ativos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS transacoes (id INTEGER PRIMARY KEY AUTOINCREMENT, data DATETIME DEFAULT (DATETIME('now', 'localtime')), tipo TEXT CHECK(tipo IN ('Compra', 'Venda')), quantidade DECIMAL, preco_pago DECIMAL, taxas DECIMAL, ativo_ref INTEGER REFERENCES ativos(id))")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS posicao (ativo INTEGER REFERENCES ativos(id), quantidade DECIMAL, preco_medio DECIMAL)")
        self.conexao.commit()

    def atualiza_lista_ativos(self):
        # CONSEGUIMOS BUSCAR OS ATIVOS MAS A FONTE É UM POUCO INSTÁVEL.
        # TODO VAMOS CHECAR SE O ATIVO A SER INSERIDO ESTÁ DISPONÍVEL NO YFINANCE ANTES DE INSERIR NO BANCO DE DADOS
        try:
            driver.get(url)
            conteudo = driver.find_element(By.CLASS_NAME, "article-content")
            res_ativos = conteudo.find_elements(By.TAG_NAME, "a")
            for ativo in res_ativos:
                ativos.append(ativo.text)
            # LISTA ATUALIZADA
            ativos.sort()
        except Exception as e:
            return f"Não foi possível atualizar a lista de ativos: {e}"

        # PARA INSERIR NO BANCO PRECISAMOS SUBTRAIR A LISTA QUE JÁ EXISTE LÁ
        # pegando lista antiga
        try:
            cursor = self.conexao.cursor()
            res_lista_antiga = cursor.execute("SELECT nome FROM ativos")
            lista_antiga = [l[0] for l in res_lista_antiga.fetchall()]

            # AGORA A GENTE VAI SUBTRAIR A PRIMEIRA LISTA DA SEGUNDA PRA TER SÓ OS ITENS ATUALIZADOS NOVOS
            lista_atualizada = list(
                set(ativos) - set(lista_antiga))
            print(lista_atualizada)

            # INSERIMOS A LISTA NOVA NO BANCO
            # precisamos transformar a lista em uma lista de tuplas
            lista_formatada = [(item,) for item in lista_atualizada]
            cursor.executemany(
                "INSERT INTO ativos (nome) VALUES (?)", lista_formatada)

            self.conexao.commit()
            return (f"{len(lista_formatada)} ativos atualizados com sucesso!")
        except Exception as e:
            return "Falha na atualização dos ativos"

    def registra_ativo(self, nome):

        # define cursor
        cursor = self.conexao.cursor()
        try:

            # procura ativo pelo nome
            res = cursor.execute(
                "SELECT * FROM ativos WHERE nome = (?)", (nome,))

            # se não encontrarmos o ativo ele é inserido
            if not res.fetchone():
                cursor.execute(
                    "INSERT INTO ativos (nome) VALUES (?)", (nome,))
                self.conexao.commit()
                return "Sucesso! Ativo inserido no banco de dados."

            # se o ativo já existir retorna falha na operação
            else:
                return "Falha na operação. Ativo já existe no banco de dados."

        # fallback em caso de erro genérico
        except Exception as e:
            return "Falha ao inserir ativo no banco de dados: ", e

    def retorna_ativos_cadastrados(self):
        cursor = self.conexao.cursor()
        res = cursor.execute("SELECT nome FROM ativos ORDER BY nome ASC")
        ativos = res.fetchall()
        return [l[0] for l in ativos]

    def retorna_preco_ativo(self, ativo):
        return yf.Ticker(f"{ativo}.SA").fast_info.last_price

    def comprar_ativo(self, nome_ativo, quantidade, taxas):

        # define cursor
        cursor = self.conexao.cursor()

        # busca o ativo pelo nome e salva o id
        ativo = cursor.execute(
            "SELECT * FROM ativos WHERE nome = (?)", (str(nome_ativo).upper(),))
        res = ativo.fetchone()

        # se o ativo não existir
        if not res:
            print("Falha na operação: o ativo deve ser inserido primeiro.")
            return

        # FAZENDO TRANSAÇÃO
        # se o ativo existir inserimos a transação
        else:
            id_ativo = res[0]
            preco = yf.Ticker(f"{nome_ativo}.SA").fast_info['last_price']
            parametros = (quantidade, preco, "Compra", taxas, id_ativo)
            cursor.execute(
                "INSERT INTO transacoes (quantidade, preco_pago, tipo, taxas, ativo_ref) VALUES (?, ?, ?, ?, ?)", parametros)
            print("Sucesso! Transação realizada com sucesso.")

            posicao = cursor.execute(
                "SELECT * FROM posicao WHERE ativo = (?)", (id_ativo,))
            res = posicao.fetchone()

            # CRIANDO OU ATUALIZANDO POSIÇÃO
            # se não tiver o ativo em posição a gente insere
            if not res:
                parametros = (id_ativo, quantidade, preco)
                cursor.execute(
                    "INSERT INTO posicao (ativo, quantidade, preco_medio) VALUES (?, ?, ?)", parametros)
                print("Posição inserida com sucesso.")

            # se a posição já existir nós atualizamos
            else:
                quantidade_antiga = res[1]
                preco_medio_antigo = res[2]
                parametros = (quantidade, self.calcula_preco_medio(
                    quantidade_antiga, preco_medio_antigo, quantidade, preco, quantidade_antiga + quantidade), id_ativo)
                cursor.execute(
                    "UPDATE posicao SET quantidade = quantidade + (?), preco_medio = (?) WHERE ativo = (?)", parametros)
                print("Posição atualizada com sucesso.")

            # salvamos as alterações no banco de dados
            self.conexao.commit()
            return "Compra realizada com sucesso!"

    def vender_ativo(self, nome_ativo, quantidade, taxas):

        # cursor
        cursor = self.conexao.cursor()

        # vamos encontrar o id do ativo pelo nome
        parametros = (str(nome_ativo).upper(),)
        ativo = cursor.execute(
            "SELECT id, nome FROM ativos WHERE nome = (?)", parametros)
        res = ativo.fetchone()

        # se o ativo não for encontrado
        if not res:
            print("Ativo não encontrado.")
            return

        # se o ativo for encontrado
        # vamos ver a posição do usuário com o ativo
        else:
            id_ativo = res[0]
            parametros = (id_ativo,)
            posicao = cursor.execute(
                "SELECT * FROM posicao WHERE ativo = (?)", parametros)
            res = posicao.fetchone()

            # se o usuário n tiver o ativo
            if not res:
                print("Erro na operação: sem posição nesse ativo")
                return

            # se tiver
            else:
                posicao_usuario = res[1]

                # se o usuario possuir menos ativos do que quer vender
                if posicao_usuario < quantidade:
                    print("Erro na operação: ativos insuficientes.")
                    return

                # se possuir mais
                else:
                    # insere transação
                    preco = yf.Ticker(
                        f"{nome_ativo}.SA").fast_info['last_price']
                    parametros = ("Venda", quantidade, preco, taxas, id_ativo)
                    cursor.execute(
                        "INSERT INTO transacoes (tipo, quantidade, preco_pago, taxas, ativo_ref) VALUES (?, ?, ?, ?, ?)", parametros)
                    print("Transação de venda inserida com sucesso!")

                    # atualiza posição
                    parametros = (quantidade, id_ativo)
                    print(posicao_usuario - quantidade)
                    if posicao_usuario - quantidade == 0:
                        cursor.execute(
                            "DELETE FROM posicao WHERE ativo = (?)", (id_ativo,))
                    else:
                        cursor.execute(
                            "UPDATE posicao SET quantidade = quantidade - (?) WHERE ativo = (?)", parametros)
                    print("Posição atualizada com sucesso!")

                    # salva no banco de dados as atualizações
                    self.conexao.commit()
                    return "Venda realizada com sucesso!"

    def calcula_preco_medio(self, qtd_antiga, precom_antigo, qtd_nova, preco_novo, qtd_total):
        precom_novo = ((qtd_antiga * precom_antigo) +
                       (qtd_nova * preco_novo)) / qtd_total
        return precom_novo

    def extrato_consolidado(self):
        df = pd.read_sql_query(
            "SELECT nome, quantidade, preco_medio FROM posicao JOIN ativos ON posicao.ativo = ativos.id", self.conexao)
        df['total_investido'] = df['quantidade'] * df['preco_medio']
        return (df)

    def relatorio_performance(self):
        extrato = self.extrato_consolidado()

        precos_api = []

        for ativo in extrato.itertuples():
            try:
                ticker = f"{ativo.nome}.SA"
                precos = yf.Ticker(ticker).fast_info.last_price
                precos_api.append(precos)
            except Exception as e:
                print(
                    "Não foi possível recuperar o preço atuao do ativo. Utilizando o preço médio salvo no banco.")
                precos_api.append(ativo.preco_medio)

        extrato['preco_mercado_atual'] = precos_api
        extrato['valor_atual'] = extrato['quantidade'] * \
            extrato['preco_mercado_atual']
        extrato['lucro/prejuizo'] = extrato['valor_atual'] - \
            extrato['total_investido']
        extrato['rentabilidade_pct'] = (
            extrato['lucro/prejuizo'] / extrato['total_investido']) * 100

        return extrato
