from typing import Callable
import os
import threading
import json
import re
import time
import sqlite3
from datetime import date

class connection():
  
  def create_socket(server_socket, host:str, port:int):
    try:
      # vincular o objeto de soquete do servidor a um endereço e porta
      server_socket.bind((host, port))
      # permitir no máximo 5 conexões em fila
      server_socket.listen(5)
      return True
    except OSError:
      print("O endereço {}:{} está em uso.".format(host, port))
      os._exit(1)

  # tentativas limitada
  def attempt(on_success:Callable, on_stop:Callable, on_fail_msg:str = '', case:bool = True, max_attempts:int = 3, delay:int = 1):
    attempts = 0
    while case:
      try:
        on_success()
        break
      except:
        if on_fail_msg:
          print(on_fail_msg)
        if attempts < max_attempts:
          on_stop()
          break
        attempts += 1
        time.sleep(delay)

  # tentativas continua
  def loop(on_success:Callable, s, delay:int):
    while not s["status"]:
      try:
        s["socket"].connect((s["host"], s["port"]))
        s["status"] = True
        on_success()
        break
      except:
        time.sleep(delay)

class validate():
  # verificar se o valor é um comando e.g. /2
  def is_command(string):
    return len(string) and re.match(r'^/\d+$', string) is not None
  # verificar se o valor é um preço valido
  def is_price(value:str) -> bool:
    try:
      float(value)
      return True
    except ValueError:
      return False
  # verifica se valor é um nome de usuario valido
  def is_username(value:str) -> bool:
    return re.match(r'^[a-zA-Z0-9]+$', value) is not None
  # verifica se é um formato de data valida
  def is_date(value:str) -> bool:
    return re.match(r'^\d{4}-\d{2}-\d{1,2}$', value) is not None
  
class console():

  group = [
    "Aleide",
    "João Paulo",
    "Gabriel",
    "Jonathas",
  ]

  commands = {
    "manager": [
      "/1 - Total de vendas de um vendedor",
      "/2 - Total de vendas de uma loja",
      "/3 - Total de vendas da rede de lojas em um período",
      "/4 - Melhor vendedor",
      "/5 - Melhor loja",
      "/0 - Sair"
    ],
    "seller": [
      "/7 - Adicionar venda",
      "/0 - Sair"
    ],
  }

  def print_intro():
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

  def print_group():
    print("\nGrupo:", ', '.join(console.group), "\n")

  def print_commands(role:str):
    print("\nComandos disponíveis:")
    for comando in console.commands[role]:
      print(comando)
    print("\t")

  def enter_price():
    value = None
    while True:
      value = input("> ")
      if validate.is_price(value):
        break
      else:
        print("O preço informado é inválido. Por favor, utilize apenas caracteres numéricos para inserir o valor")
    return value

  def enter_username():
    value = None
    while True:
      value = input("> ").lower()
      if validate.is_username(value):
        break
      else:
        print("O nome de usuário informado é inválido. Por favor, não utilize caracteres especiais ou espaços.")
    return value

  def enter_date():
    value = None
    while True:
      value = input("> ")
      if validate.is_date(value):
        break
      else:
        print("A data informada é inválida. Por favor, atente-se ao formato (AAAA-MM-DD).")
    return value

  def enter_auth():
    m = {}
    print("Digite o nome de usuário:")
    m["username"] = console.enter_username()
    print("Digite a senha:")
    m["password"] = input("> ")
    return m

  def enter_sale():
    m = {}
    print("Digite o nome da loja:")
    m["store"] = input("> ")
    print("Digite o valor:")
    m["price"] = console.enter_price()
    m["date"] = str(date.today())
    return m

  def enter_period():
    m = {}
    print("Digite a data minima(AAAA-MM-DD):")
    m["min"] = console.enter_date()
    print("Digite a data maxima(AAAA-MM-DD):")
    m["max"] = console.enter_date()
    return m
  
  def send(cs, code, data = None):
    cs.send(json.dumps([code, data]).encode())

  def recv(cs):
    try:
      data = json.loads(cs.recv(1024).decode())
    except:
      return [None, None]
    return data

class database():
  def __init__(self, name:str):
    self.name = name

  # conectar o banco de dados
  def connect(self):
    self.banco = sqlite3.connect(self.name, check_same_thread=False)
    self.cursor = self.banco.cursor()

  # inserção em massa de dados
  def bulk_insert(self):
    # tabela de usuarios
    self.cursor.execute("CREATE TABLE IF NOT EXISTS users (id integer PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, name TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'seller')")
    # tabela de vendas
    self.cursor.execute("CREATE TABLE IF NOT EXISTS sales (id integer PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, store TEXT NOT NULL, date text NOT NULL, price float NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id))")
   
    # adicionar o gerente Jess
    self.add_user('jess', '123', 'Jess', role="manager")
    # adicionar vendedor Carl e algumas vendas
    user_id = self.add_user('carl', '123', 'Carl', role="seller")
    self.add_sale('americanas', '2023-05-09', 300, user_id)
    self.add_sale('americanas', '2023-05-07', 700, user_id)
    # adicionar vendedor Paul e algumas vendas
    user_id = self.add_user('paul', '123', 'Paul', role="seller")
    self.add_sale('americanas', '2023-05-09', 200, user_id)
    self.add_sale('bompreco', '2023-05-08', 600, user_id)

    self.banco.commit()
    
  # obter todos os usuarios
  def login(self, username:str, password:str) -> bool:
    consulta_sql = "SELECT id, name, role FROM users WHERE username = ? AND password = ? LIMIT 1"
    self.cursor.execute(consulta_sql, (username,password))
    return self.cursor.fetchone()

  # obter o id do usuario pelo nome do usuário
  def get_userid(self, username:str) -> bool:
    self.cursor.execute(f"SELECT id FROM users WHERE username = '{username}'")
    return self.cursor.fetchone()[0]
  
  # adicionar usuario
  def add_user(self, username:str, password:str, name:str, role:str = "seller") -> int:
    self.cursor.execute(f"INSERT INTO users (username, password, name, role) VALUES ('{username}', '{password}', '{name}', '{role}')")
    return self.cursor.lastrowid
  
  # adicionar venda
  def add_sale(self, store:str, date:str, price:float, user_id:int):
    self.cursor.execute(f"INSERT INTO sales (user_id, store, date, price) VALUES ('{user_id}', '{store}', '{date}', {price})")
    return self.cursor.rowcount > 0

  # limpar as tabelas de usuários e vendas
  def clear(self):
    if self.has_table('users'):
      self.cursor.execute("DELETE FROM users")
      
    if self.has_table('sales'):
      self.cursor.execute("DELETE FROM sales")
  
  # verificar se tabela existe
  def has_table(self, name:str) -> bool:
    self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{name}'")
    return self.cursor.fetchone() is not None

  # total de vendas de uma loja
  def get_total_store_sales(self, store:str):
    consulta_sql = "SELECT COUNT(*), SUM(price) FROM sales WHERE store = ?"
    self.cursor.execute(consulta_sql, (store,))
    return self.cursor.fetchone()
  
  # verificar se loja existe
  def has_store(self, name:str) -> bool:
    consulta_sql = "SELECT 1 FROM sales WHERE store = ? LIMIT 1"
    self.cursor.execute(consulta_sql, (name,))
    return self.cursor.fetchone() is not None
  
  # verificar se vendedor existe
  def has_seller(self, username:str) -> bool:
    consulta_sql = "SELECT 1 FROM users WHERE username = ? AND role = 'seller' LIMIT 1"
    self.cursor.execute(consulta_sql, (username,))
    return self.cursor.fetchone() is not None
  
  # total de vendas de um vendedor
  def get_total_seller_sales(self,username:str):
    self.cursor.execute("""
        SELECT users.name, COUNT(sales.id) AS total_vendas, SUM(sales.price) AS soma_vendas
        FROM users
        LEFT JOIN sales ON users.id = sales.user_id
        WHERE users.username = ?
        GROUP BY users.name;
    """, (username,))
    return self.cursor.fetchone()

  # total de vendas da rede de lojas em um período
  def get_total_period_salles(self, data_inicial:str, data_final:str):
    consulta_sql = "SELECT COUNT(*), SUM(price) FROM sales WHERE date BETWEEN ? AND ?"
    self.cursor.execute(consulta_sql, (data_inicial, data_final))
    return self.cursor.fetchone()

  # melhor vendedor (aquele que tem o maior valor acumulado de vendas)
  def get_best_seller(self):
    self.cursor.execute("""
      SELECT users.name, COUNT(*) AS total_count, SUM(sales.price) AS total_vendas
      FROM users
      INNER JOIN sales ON users.id = sales.user_id
      GROUP BY users.id
      ORDER BY total_vendas DESC
      LIMIT 1;
  """)
    return self.cursor.fetchone()
    
  # melhor loja (aquela que tem o maior valor acumulado de vendas)
  def get_best_store(self):
    consulta_sql = "SELECT store, COUNT(*), SUM(price) as total_vendas FROM sales GROUP BY store ORDER BY total_vendas DESC LIMIT 1"
    self.cursor.execute(consulta_sql)
    return self.cursor.fetchone()
