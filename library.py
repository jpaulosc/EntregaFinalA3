import random
import socket
import threading
import sqlite3
import json
import os
import csv
from constants import consts
import re

TRANSLATIONS = {}

def _(code:str) -> str :
  global TRANSLATIONS
  filename = 'translation.json'
  # verificar se o objeto não está preenchido e se o arquivo existe.
  if not TRANSLATIONS and os.path.exists(filename):
    # importar arquivo json com caracteres acentuados
    with open(filename, 'r', encoding='utf-8') as arquivo:
      TRANSLATIONS = json.load(arquivo)
      return TRANSLATIONS[code] or code
  else:
    return TRANSLATIONS[code] or code

class helper():
  
  def export_csv(self, dados:list):
    with open('exports/data.csv', 'w', newline='') as arquivo:
      writer = csv.writer(arquivo)
      writer.writerows(dados)

  def validate_price(value:str) -> bool:
    try:
      float(value)
      return True
    except ValueError:
      return False

  def validate_username(value:str) -> bool:
    return re.match(r'^[a-zA-Z0-9]+$', value) is not None

  def validate_date(value:str) -> bool:
    return re.match(r'^\d{4}-\d{2}-\d{1,2}$', value) is not None

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
    self.cursor.execute("CREATE TABLE IF NOT EXISTS users (id integer PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, name TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'seller')")
    # tabela de vendas
    self.cursor.execute("CREATE TABLE IF NOT EXISTS sales (id integer PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, shopname TEXT NOT NULL, date text NOT NULL, price float NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id))")
   
    # gerente Jess
    self.add_user('jess', '123', 'Jess', consts.MANAGER)
    # vendedor Carl
    user_id = self.add_user('carl', '123', 'Carl', consts.SELLER)
    self.add_sale('americanas', '2023-05-09', 300, user_id)
    self.add_sale('americanas', '2023-05-07', 700, user_id)
    # vendedor Paul
    user_id = self.add_user('paul', '123', 'Paul', consts.SELLER)
    self.add_sale('americanas', '2023-05-09', 200, user_id)
    self.add_sale('bompreco', '2023-05-08', 600, user_id)
    
  # obter todos os usuarios
  def login(self, username:str, password:str) -> bool:
    consulta_sql = "SELECT id, name, role FROM users WHERE username = ? AND password = ? LIMIT 1"
    self.cursor.execute(consulta_sql, (username,password))
    return self.cursor.fetchone()

  def add_user(self, username:str, password:str, name:str, role:str = consts.SELLER) -> int:
    self.cursor.execute(f"INSERT INTO users (username, password, name, role) VALUES ('{username}', '{password}', '{name}', '{role}')")
    return self.cursor.lastrowid
  
  def add_sale(self, shopname:str, date:str, price:float, user_id:int):
    self.cursor.execute(f"INSERT INTO sales (user_id, shopname, date, price) VALUES ('{user_id}', '{shopname}', '{date}', {price})")
    self.banco.commit()

  # limpar tabela
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
  def get_total_vendas_loja(self, shopname:str):
    consulta_sql = "SELECT COUNT(*), SUM(price) FROM sales WHERE shopname = ?"
    self.cursor.execute(consulta_sql, (shopname,))
    return self.cursor.fetchone()
  
  # verificar se loja existe
  def has_loja(self, name:str) -> bool:
    consulta_sql = "SELECT 1 FROM sales WHERE shopname = ? LIMIT 1"
    self.cursor.execute(consulta_sql, (name,))
    return self.cursor.fetchone() is not None
  
  # verificar se vendedor existe
  def has_vendedor(self, username:str) -> bool:
    consulta_sql = "SELECT 1 FROM users WHERE username = ? AND role = 'seller' LIMIT 1"
    self.cursor.execute(consulta_sql, (username,))
    return self.cursor.fetchone() is not None
  
  # total de vendas de um vendedor
  def get_total_vendas_vendedor(self,username:str):
    self.cursor.execute("""
        SELECT users.name, COUNT(sales.id) AS total_vendas, SUM(sales.price) AS soma_vendas
        FROM users
        LEFT JOIN sales ON users.id = sales.user_id
        WHERE users.username = ?
        GROUP BY users.name;
    """, (username,))
    return self.cursor.fetchone()
    
  # total de vendas da rede de lojas em um período
  def get_total_vendas_periodo(self, data_inicial:str, data_final:str):
    consulta_sql = "SELECT COUNT(*), SUM(price) FROM sales WHERE date BETWEEN ? AND ?"
    self.cursor.execute(consulta_sql, (data_inicial, data_final))
    return self.cursor.fetchone()

  # melhor vendedor (aquele que tem o maior valor acumulado de vendas)
  def get_melhor_vendedor(self):
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
  def get_melhor_loja(self):
    consulta_sql = "SELECT shopname, COUNT(*), SUM(price) as total_vendas FROM sales GROUP BY shopname ORDER BY total_vendas DESC LIMIT 1"
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
    consts.MANAGER: [
      '{:d} - {}'.format(consts.COM_SELLER_TOTAL_SALES, _("seller.total.sales")),
      '{:d} - {}'.format(consts.COM_SHOP_TOTAL_SALES, _("shop.total.sales")),
      '{:d} - {}'.format(consts.COM_TOTAL_SALES_PERIOD, _("total.sales.period")),
      '{:d} - {}'.format(consts.COM_BEST_SELLER, _("best.seller")),
      '{:d} - {}'.format(consts.COM_BEST_SHOP, _("best.shop")),
      '{:d} - {}'.format(consts.COM_EXIT, _("exit"))
    ],
    consts.SELLER: [
      '{:d} - {}'.format(consts.COM_ADD_SALE, _("add.sale")),
      '{:d} - {}'.format(consts.COM_EXIT, _("exit"))
    ],
    "admin": [
      '{:d} - {}'.format(consts.COM_ACTIVE_CLIENTS, _("active.clients")),
      '{:d} - {}'.format(consts.COM_LOGGED_USERS, _("logged.users")),
      '{:d} - {}'.format(consts.COM_SIMULATE_CONNECTION_FAILURE, _("simulate.connection.failure")),
      '{:d} - {}'.format(consts.COM_EXIT, _("shutdown"))
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
  
  def print_notificacao(filename:str):
    print("USAGE: python {} <IP> <Port>".format(filename))
    print("EXAMPLE: python {} localhost 8000".format(filename))

  def print_comandos(role:str):
    print(_("commands.available"))
    for comando in console.comandos[role]:
      print(comando)
    print("\t")