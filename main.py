import pandas as pd
import os
import sqlite3


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
            "CREATE TABLE IF NOT EXISTS ativos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE, tipo TEXT CHECK(tipo IN ('Ação', 'Fundo Imobiliário', 'Cripto')))")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS transacoes (id INTEGER PRIMARY KEY AUTOINCREMENT, data DATETIME DEFAULT (DATETIME('now', 'localtime')), quantidade DECIMAL, preco_pago DECIMAL, taxas DECIMAL, ativo_ref INTEGER REFERENCES ativos(id))")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS posicao (ativo INTEGER REFERENCES ativos(id), quantidade DECIMAL, preco_medio DECIMAL)")
        self.conexao.commit()

    def registra_ativo(self, nome, tipo):
        cursor = self.conexao.cursor()
        try:
            res = cursor.execute(
                "SELECT * FROM ativos WHERE nome = (?)", (nome,))
            if not res.fetchone():
                cursor.execute(
                    "INSERT INTO ativos (nome, tipo) VALUES (?, ?)", (nome, tipo))
                self.conexao.commit()
                print("Sucesso! Ativo inserido no banco de dados.")
            else:
                print("Falha na operação. Ativo já existe no banco de dados.")
        except Exception as e:
            print("Falha ao inserir ativo no banco de dados: ", e)

    def comprar_ativo(self, nome_ativo, quantidade, preco, taxas):

        # define cursor
        cursor = self.conexao.cursor()

        # busca o ativo pelo nome e salva o id
        ativo = cursor.execute(
            "SELECT * FROM ativos WHERE nome = (?)", (nome_ativo,))
        res = ativo.fetchone()

        # se o ativo não existir
        if not res:
            print("Falha na operação: ativo não encontrado.")
            return

        # FAZENDO TRANSAÇÃO
        # se o ativo existir inserimos a transação
        else:
            id_ativo = res[0]

            parametros = (quantidade, preco, taxas, id_ativo)
            cursor.execute(
                "INSERT INTO transacoes (quantidade, preco_pago, taxas, ativo_ref) VALUES (?, ?, ?, ?)", parametros)
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

    def calcula_preco_medio(self, qtd_antiga, precom_antigo, qtd_nova, preco_novo, qtd_total):
        precom_novo = ((qtd_antiga * precom_antigo) +
                       (qtd_nova * preco_novo)) / qtd_total
        return precom_novo


gestao = GerenciadorInvestimento()
gestao.registra_ativo("PETR4", "Ação")
gestao.comprar_ativo("PETR4", 3, 10, 5)
