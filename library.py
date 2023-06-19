import random
import socket
import threading
import sqlite3
import json
from constants import consts

class app:

  COMMAND_CODE = None
  INPUT_PREFIX = ''
        
  def command_code(self) -> bool :
    codigo = input(f"{self.INPUT_PREFIX}")
    if codigo.isdigit():
      self.COMMAND_CODE = int(codigo)
      return True
    else:
      console.print_alerta("Entrada inválida. Por favor insira um número válido.")
    return False

class helper():
  def get_random_open_port():
    result = None
    while True:
      port = random.randint(1024, 65535)  # Choose a random port number
      with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
          s.bind(('localhost', port))
          result = port
          break 
        except socket.error:
          pass
    return result

class database():
  def __init__(self, name:str):
    self.name = name
    self.thread_local = threading.local()

  def connect(self):
    self.banco = sqlite3.connect(self.name, check_same_thread=False)
    self.cursor = self.banco.cursor()

  # inserção em massa
  def bulk_insert(self):
    # tabela de usuarios
    self.cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (id integer PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, name TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'vendedor')")
    # tabela de vendas
    self.cursor.execute("CREATE TABLE IF NOT EXISTS vendas (id integer PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, loja TEXT NOT NULL, data text NOT NULL, valor float NOT NULL, FOREIGN KEY (user_id) REFERENCES usuarios(id))")
   
    # gerente Jess
    self.add_usuario('jess', '123', 'Jess', 'gerente')
    # vendedor Carl
    user_id = self.add_usuario('carl', '123', 'Carl', 'vendedor')
    self.add_venda('americanas', '2023-05-09', 300, user_id)
    self.add_venda('americanas', '2023-05-07', 700, user_id)
    # vendedor Paul
    user_id = self.add_usuario('paul', '123', 'Paul', 'vendedor')
    self.add_venda('americanas', '2023-05-09', 200, user_id)
    self.add_venda('bompreco', '2023-05-08', 600, user_id)

    self.banco.commit()
    
  # obter todos os usuarios
  def login(self, username:str, password:str, host:str, port:str) -> bool:
    consulta_sql = "SELECT id, name, role FROM usuarios WHERE username = ? AND password = ? LIMIT 1"
    self.cursor.execute(consulta_sql, (username,password))
    return self.cursor.fetchone()

  def add_usuario(self, username:str, password:str, name:str, role:str = 'vendedor') -> int:
    self.cursor.execute(f"INSERT INTO usuarios (username, password, name, role) VALUES ('{username}', '{password}', '{name}', '{role}')")
    return self.cursor.lastrowid
  
  def get_usuarios_logado(self):
    self.cursor.execute("SELECT username, name, host, port FROM usuarios WHERE host IS NOT NULL AND port IS NOT NULL ORDER BY port")
    users = self.cursor.fetchall()
    return users
  
  def add_venda(self, loja:str, data:str, valor:float, user_id:int = None):
    user_id = self.user[0] if user_id is None else user_id
    self.cursor.execute(f"INSERT INTO vendas (user_id, loja, data, valor) VALUES ('{user_id}', '{loja}', '{data}', {valor})")

  # limpar tabela
  def clear(self):
    self.cursor.execute("DELETE FROM usuarios")
    self.cursor.execute("DELETE FROM vendas")
  
  # total de vendas de uma loja
  def get_total_vendas_loja(self, loja:str):
    consulta_sql = "SELECT COUNT(*), SUM(valor) FROM vendas WHERE loja = ?"
    self.cursor.execute(consulta_sql, (loja,))
    return self.cursor.fetchone()
  
  # verificar se loja existe
  def has_loja(self, nome:str) -> bool:
    consulta_sql = "SELECT 1 FROM vendas WHERE loja = ? LIMIT 1"
    self.cursor.execute(consulta_sql, (nome,))
    return self.cursor.fetchone() is not None
  
  # verificar se vendedor existe
  def has_vendedor(self, username:str) -> bool:
    consulta_sql = "SELECT 1 FROM usuarios WHERE username = ? AND role = 'vendedor' LIMIT 1"
    self.cursor.execute(consulta_sql, (username,))
    return self.cursor.fetchone() is not None
  
  # total de vendas de um vendedor
  def get_total_vendas_vendedor(self,username:str):
    #consulta_sql = "SELECT COUNT(*), SUM(valor) FROM vendas WHERE user_id = ?"
    self.cursor.execute("""
        SELECT usuarios.name, COUNT(vendas.id) AS total_vendas, SUM(vendas.valor) AS soma_vendas
        FROM usuarios
        LEFT JOIN vendas ON usuarios.id = vendas.user_id
        WHERE usuarios.username = ?
        GROUP BY usuarios.name;
    """, (username,))
    return self.cursor.fetchone()
    
  # total de vendas da rede de lojas em um período
  def get_total_vendas_periodo(self, data_inicial:str, data_final:str):
    consulta_sql = "SELECT COUNT(*), SUM(valor) FROM vendas WHERE data BETWEEN ? AND ?"
    self.cursor.execute(consulta_sql, (data_inicial, data_final))
    return self.cursor.fetchone()

  # melhor vendedor (aquele que tem o maior valor acumulado de vendas)
  def get_melhor_vendedor(self):
    self.cursor.execute("""
      SELECT usuarios.name, COUNT(*) AS total_count, SUM(vendas.valor) AS total_vendas
      FROM usuarios
      INNER JOIN vendas ON usuarios.id = vendas.user_id
      GROUP BY usuarios.id
      ORDER BY total_vendas DESC
      LIMIT 1;
  """)
    return self.cursor.fetchone()
    
  # melhor loja (aquela que tem o maior valor acumulado de vendas)
  def get_melhor_loja(self):
    consulta_sql = "SELECT loja, COUNT(*), SUM(valor) as total_vendas FROM vendas GROUP BY loja ORDER BY total_vendas DESC LIMIT 1"
    self.cursor.execute(consulta_sql)
    return self.cursor.fetchone()
 
class console():

  OKBLUE = '\033[94m'
  OKCYAN = '\033[96m'
  OKGREEN = '\033[92m'
  WARNING = '\033[93m'
  FAIL = '\033[91m'
  ENDC = '\033[0m'
  BOLD = '\033[1m'
  UNDERLINE = '\033[4m'

  comandos = {
    "gerente": [
      str(consts.COM_SELLER_TOTAL_SALES) + " - Total de vendas de um vendedor",
      str(consts.COM_SHOP_TOTAL_SALES ) + " - Total de vendas de uma loja",
      str(consts.COM_TOTAL_SALES_PERIOD) + " - Total de vendas da rede de lojas em um período",
      str(consts.COM_BEST_SELLER) + " - Melhor vendedor",
      str(consts.COM_BEST_SHOP) + " - Melhor loja",
      str(consts.COM_EXIT) + " - Sair"
    ],
    "vendedor": [
      str(consts.COM_ADD_SALE ) + " - Adicionar venda",
      str(consts.COM_EXIT) + " - Sair"
    ],
    "admin": [
      str(consts.COM_ACTIVE_CLIENTS) + " - Clientes ativos",
      str(consts.COM_LOGGED_USERS) + " - Usuarios logados",
      str(consts.COM_SIMULATE_CONNECTION_FAILURE) + " - Simular falha de conexão com o servidor",
      str(consts.COM_EXIT) + " - Encerrar"
    ]
  }

  def intro():
    print("""
      _____           _      _                ____  
    |  __ \         (_)    | |         /\   |___ \ 
    | |__) | __ ___  _  ___| |_ ___   /  \    __) |
    |  ___/ '__/ _ \| |/ _ \ __/ _ \ / /\ \  |__ < 
    | |   | | | (_) | |  __/ || (_) / ____ \ ___) |
    |_|   |_|  \___/| |\___|\__\___/_/    \_\____/ 
                    _/ |                            
                  |__/                             
    """)

  def print_info(txt:str):
    print(console.OKBLUE + txt + console.ENDC)
  
  def print_alerta(txt:str):
    print(console.WARNING + txt + console.ENDC)
  
  def print_erro( txt:str):
    print(console.FAIL + txt + console.ENDC)
  
  def print_sucesso(txt:str):
    print(console.OKGREEN + txt + console.ENDC)
  
  def sprint_thebest(strf:str, str1:str, str2:int, str3:float):
    return f"{strf} {console.OKCYAN}{str1}{console.ENDC} com o total de {console.OKCYAN}{int(str2)} venda(s){console.ENDC}, totalizando {console.OKCYAN}R$ {float(str3)}{console.ENDC}"

  def print_notificacao(filename:str):
    print(f"USAGE: python {filename} <IP> <Port>")
    print(f"EXAMPLE: python {filename} localhost 8000")

  def print_comandos(cargo:str):
    print("\nComandos disponíveis:")
    for comando in console.comandos[cargo]:
      print(comando)
    print("\t")