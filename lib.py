import socket
import json
import threading
import os
import sqlite3

class database():
  def __init__(self, name:str):
    self.name = name
    self.user = None
    
  def connect(self):
    banco = sqlite3.connect(self.name, check_same_thread=False)
    self.cursor = banco.cursor()

  # inserção em massa
  def bulk_insert(self):
    # tabela de usuarios
    self.cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (id integer PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, name TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'vendedor')")
     # tabela de vendas
    self.cursor.execute("CREATE TABLE IF NOT EXISTS vendas (id integer PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, loja TEXT NOT NULL, data text NOT NULL, valor float NOT NULL, FOREIGN KEY (user_id) REFERENCES usuarios(id))")
   
    self.clear()

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

  # obter todos os usuarios
  def login(self, username:str, password:str) -> bool:
    consulta_sql = "SELECT id, name, role, username FROM usuarios WHERE username = ? AND password = ? LIMIT 1"
    self.cursor.execute(consulta_sql, (username,password))
    resultado = self.cursor.fetchone()
    if resultado is not None:
      self.user = resultado
    return resultado is not None
  
  def is_logado(self):
    return self.user is not None
  
  def add_usuario(self, username:str, password:str, name:str, role:str = 'vendedor') -> int:
    self.cursor.execute(f"INSERT INTO usuarios (username, password, name, role) VALUES ('{username}', '{password}', '{name}', '{role}')")
    return self.cursor.lastrowid
  
  def add_venda(self, loja:str, data:str, valor:float, user_id:int = None):
    user_id = self.user if user_id is None else user_id
    self.cursor.execute(f"INSERT INTO vendas (user_id, loja, data, valor) VALUES ('{user_id}', '{loja}', '{data}', {valor})")

  def get_userid(self, username:str):
    self.cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
    resultado = self.cursor.fetchone()
    return resultado[0] if resultado is not None else None
  
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
  def has_vendedor(self, id:int|str) -> bool:
    if isinstance(id, int):
      consulta_sql = "SELECT 1 FROM usuarios WHERE id = ? AND role = 'vendedor' LIMIT 1"
    elif isinstance(id, str):
      consulta_sql = "SELECT 1 FROM usuarios WHERE username = ? AND role = 'vendedor' LIMIT 1"

    self.cursor.execute(consulta_sql, (id,))
    return self.cursor.fetchone() is not None
  
  # total de vendas de um vendedor
  def get_total_vendas_vendedor(self,user_id:int):
    #consulta_sql = "SELECT COUNT(*), SUM(valor) FROM vendas WHERE user_id = ?"
    self.cursor.execute("""
        SELECT usuarios.name, COUNT(vendas.id) AS total_vendas, SUM(vendas.valor) AS soma_vendas
        FROM usuarios
        LEFT JOIN vendas ON usuarios.id = vendas.user_id
        WHERE usuarios.id = ?
        GROUP BY usuarios.name;
    """, (user_id,))
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
  
class servidor():
  def __init__(self, host:str, port:int, db:str):

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    
    print(f"Servidor iniciado. Aguardando conexões na porta {port}...")

    self.server_socket = server_socket
    self.db = db

  # Função para lidar com a conexão de um cliente
  def __handle_client(self, client_socket):

    db = database(self.db)
    db.connect()
    db.bulk_insert()

    while True:
      data = client_socket.recv(1024).decode()
      cod = 0

      # Identifica o tipo de cliente
      if data != None and data != '':
        data = json.loads(data)
        # código de operação
        cod = int(data.get("code"))

      match cod:
        # total de vendas de um vendedor
        case 1:
          username = data.get("username")
          if db.has_vendedor(username):
            user_id = db.get_userid(username)
            value = db.get_total_vendas_vendedor(user_id)
            client_socket.send(f"O vendedor {value[0]} realizou no total {int(value[1])} venda(s), totalizando R$ {float(value[2])}".encode())
          else: 
            client_socket.send(f"O vendedor {username} não existe.".encode())
        # total de vendas de uma loja
        case 2:
          nome = data.get("nome")
          if db.has_loja(nome):
            value = db.get_total_vendas_loja(nome)
            client_socket.send(f"A loja {nome} teve no total {int(value[0])} venda(s), totalizando R$ {float(value[1])}".encode())
          else: 
            client_socket.send(f"A loja {nome} não existe.".encode())
        # total de vendas da rede de lojas em um período
        case 3:
          min = data.get("min")
          max = data.get("max")
          value = db.get_total_vendas_periodo(data.get("min"), data.get("max"))
          client_socket.send(f"O total de vendas da rede de lojas entre o periodo de {min} e {max} foi de {int(value[0])}, totalizando R$ {float(value[1])}".encode())
        # melhor vendedor (aquele que tem o maior valor acumulado de vendas)
        case 4:
          value = db.get_melhor_vendedor()
          client_socket.send(f"O melhor vendedor foi {value[0]} com o total de {int(value[1])} venda(s), totalizando R$ {float(value[2])}".encode())
        # melhor loja (aquela que tem o maior valor acumulado de vendas)
        case 5:
          value = db.get_melhor_loja()
          client_socket.send(f"A melhor loja foi {value[0]} com o total de {int(value[1])} venda(s), totalizando R$ {float(value[2])}".encode())
        case 6:
          db.add_venda(data.get("loja"), data.get("data"), data.get("valor"))
          client_socket.send("Dados inseridos com sucesso!".encode())
        case 7:
          check = db.login(data.get("username"), data.get("password"))
          if check:
            client_socket.send(json.dumps(db.user).encode())
          else:
            client_socket.send("0".encode())
        case _:
          print('Fechando a conexao')
          client_socket.send("Conexão encerrada.".encode())
          client_socket.close()
          # remover todos os dados inseridos
          db.clear()
          os._exit(1)
      
  # Função para lidar com as conexões de clientes
  def __handle_connections(self):
    while True:
      # Aguarda a conexão de um cliente
      client_socket, addr = self.server_socket.accept()
      print(f"Nova conexão estabelecida em: {addr}")
          
      # Inicia uma nova thread para lidar com o cliente
      client_thread = threading.Thread(target=self.__handle_client, args=(client_socket,))
      client_thread.start()
      
  def conectar(self):
    return False

  def iniciar(self):
    connections_thread = threading.Thread(target=self.__handle_connections)
    connections_thread.start()

class console():
  HEADER = '\033[95m'
  OKBLUE = '\033[94m'
  OKCYAN = '\033[96m'
  OKGREEN = '\033[92m'
  WARNING = '\033[93m'
  FAIL = '\033[91m'
  ENDC = '\033[0m'
  BOLD = '\033[1m'
  UNDERLINE = '\033[4m'

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
  
  def set(self):
    return False