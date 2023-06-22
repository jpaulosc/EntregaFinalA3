from typing import Callable
import socket
import threading
from src.library import *

BRIDGE_SERVER = {
	"host": "localhost",
	"port": 8061,
	"status": False,
}

TEMP_SERVER = {
	"host": "localhost",
	"port": 8082,
	"status": False,
}

class server():
  def __init__(self, database:database):
    self.db = database
    self.db.connect()
     
  def init(self, main_server, message:str):
    host = main_server["host"]
    port = main_server["port"]

    # criar um objeto de soquete do servidor
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.create_socket(server_socket, host, port)
    print(message.format(host, port))
    threading.Thread(target=self.sign_in, args=(server_socket,)).start()

  def sign_in(self, server_socket):
    self.clients = clients()
    self.clients.accept(server_socket,on_sign=self.on_client_connect, on_request=self.resolve)

  # evento de conexão
  def on_client_connect(self, client_socket, alias:str):
    print(f"O cliente {alias} se conectou ao servidor")

  # resolver solicitações e enviar respostas
  def resolve(self, code:str, alias:str, data, client_socket):
    s = self.clients.get(data["client_socket"])
    match code:
      case "/1":
        name = data.get("username")
        if self.db.has_seller(name):
          name, sales, total = self.db.get_total_seller_sales(name)
          console.send(s, "O vendedor {} realizou no total {} venda(s), totalizando R$ {:.2f}".format(name, sales, total), data)
        else: 
          console.send(s,"O vendedor '{}' não existe. Tente novamente.".format(name), data)
      case "/2":
        name = data.get("name")
        if self.db.has_store(name):
          sales, total = self.db.get_total_store_sales(name)
          console.send(s,"A loja {} teve no total {:d} venda(s), totalizando R$ {:.2f}".format(name, sales, total), data)
        else: 
          console.send(s,"A loja '{}' não existe. Tente novamente.".format(name), data)
      case "/3":
        min = data.get("min")
        max = data.get("max")
        sales, total = self.db.get_total_period_salles(min, max)
        message = "O total de venda(s) da rede de lojas entre o periodo de {} e {} foi de {:d}, totalizando R$ {:.2f}".format(min, max, sales, total)
        console.send(s,message, data)
      case "/4":
        name, sales, total = self.db.get_best_seller()
        message = "O melhor vendedor foi {} com o total de {:d} venda(s), totalizando R$ {:.2f}".format(name, sales, total)
        console.send(s,message, data)
      case "/5":
        name, sales, total = self.db.get_best_store()
        message = "A melhor loja foi {} com o total de {:d} venda(s), totalizando R$ {:.2f}".format(name, sales, total)
        console.send(s,message, data)
      case "/7":
        userdata = data.get("userdata")
        price = data.get("price")
        store = data.get("store")
        self.db.add_sale(store, data.get("date"), price, userdata["id"])
        self.db.banco.commit()
        console.send(s,"Venda adicionada com sucesso!", data)
        self.clients.broadcast(data["client_socket"], f"O vendedor {userdata['name']} da loja {store} adicionou uma venda de {price}.")
      case _:
          console.send(s,"Comando desconhecido.", data)
      
  def reconnect(main_server, on_success:Callable, delay:int = 1):
    threading.Thread(target=connection.loop, args=(on_success,main_server, delay,)).start()

class client:

  # dados do usuarios logado
  USERDATA = None

  def request(self, client_socket, auth):
    
    if auth and self.USERDATA is None:
      db = database('src/database.sq3')
      db.connect()
      print("Digite o seu nome de usuário e senha para prosseguir.\n")
      while self.USERDATA is None:
        data = console.enter_auth()
        username = data.get("username")
        userdata = db.login(username, data.get("password"))
        if userdata is not None:
            id, name, role = userdata
            self.USERDATA = {
			        "id": id, 
              "prefix": f"{username}@projetoa3",
			        "username": username, 
			        "name": name, 
			        "role": role
				    }
            print("\nAutenticado com sucesso!")
            console.print_commands(role)
            break
        else:
          print("Nome de usuario ou senha invalido")
        
    while True:
      value = input("")

      if value == "/0":
        client_socket.close()
        print("Desconectado do servidor.")
        break
      
      v = {}
      if validate.is_command(value):
        match self.USERDATA["role"]:
          case "seller":
            match value:
              case "/7":
                v = console.enter_sale()
              case _:
                print("Código de comando inválido")
                continue
          case "manager":
            match value:
              case "/1":
                print("Digite o nome de usuário do vendedor:")
                v["username"] = console.enter_username()
              case "/2":
                print("Digite o nome da loja:")
                v["name"] = input("> ").lower()
              case "/3":
                v = console.enter_period()
              case _:
                if value not in ["/4", "/5"]:
                  print("Código de comando inválido")
                  continue
          
      v["userdata"] = self.USERDATA
        
      console.send(client_socket, value, v)

  def response(self, client_socket):
    while True:
      code, data = console.recv(client_socket)
      if code is None:
        break
      else:
        print(f"{code}\r")
          

class agent(client):

  def connect(self, data):
    data["socket"] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    self.s = data
    self.s["socket"].connect((self.s["host"], self.s["port"]))
    self.s["status"] = True
                
    console.print_intro()
    console.print_group()
    self.interate(self.s["socket"], authenticate=True)

  def interate(self, client_socket, authenticate:bool=False, on_send:Callable = None):
    if on_send and callable(on_send):
      receive_thread = threading.Thread(target=on_send, args=(client_socket,))
    else:
      receive_thread = threading.Thread(target=self.response, args=(client_socket,))
    
    send_thread = threading.Thread(target=self.request, args=(client_socket,authenticate,))
    receive_thread.start()
    send_thread.start()

class clients:
  
  store = {}
        
  def handle(self, client_socket, alias:str, address:list, on_request:Callable = None):
  
    while True:
      code, data = console.recv(client_socket)
      if code is None:
        print(f"Cliente {address} desconectado.")
        self.remove(client_socket, alias)
        break
      else:
        if validate.is_command(code):
          if on_request and callable(on_request):
            on_request(code, alias, data, client_socket)
        else:
          message = code
          message = f"{alias}: {message}" if data["userdata"] is None else f"{ data['userdata']['prefix']}: {message}"
          self.broadcast(alias, message)
          
        #print(code, data)
        print(f"Mensagem recebida do cliente {address}")

  # habilitar conexão do cliente
  def accept(self, server_socket, on_sign:Callable = None, on_request:Callable = None):
    while True:
      client_socket, address = server_socket.accept()
      print(f"Cliente {address} conectado.")
      alias = self.add(address, client_socket)
      if on_sign and callable(on_sign):
        on_sign(client_socket, alias)
      threading.Thread(target=self.handle, args=(client_socket, alias, address,on_request,)).start()

  # remover todos os clientes
  def remove_all(self):
    for alias in self.store:
      client_socket = self.store[alias]
      self.remove(client_socket, alias)
      
  def get(self, alias:str):
    return self.store[alias]

  # remover cliente
  def remove(self, client_socket, alias:str):
    client_socket.close()
    del self.store[alias]

  # adicionar cliente
  def add(self, address:list, client) -> str:
    host, port = address
    alias = f"{host}@{port}"
    self.store[alias] = client
    return alias

  # enviar mensagens a todo os clientes conectado
  def broadcast(self, sender_alias:str, message):
    for alias in self.store:
      client_socket = self.store[alias]
      if alias != sender_alias:
        try:
          console.send(client_socket, message)
        except:
          self.remove(client_socket, alias)

class bridge_server:
  def __init__(self, main_server, temp_server, bridge_server):

    # main server client socket
    self.ms = main_server
    self.ms["socket"] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # temp server client socket
    self.ts = temp_server
    self.ts["socket"] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # bridge server client socket
    self.bs = bridge_server
    self.bs["socket"] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  def start(self):
    host = self.bs["host"]
    port = self.bs["port"]

    connection.create_socket(self.bs["socket"], host, port)
    self.bs["status"] = True

    threading.Thread(target=self.run).start()
    threading.Thread(target=self.attempt).start()

  def run(self):
    self.clients = clients()
    self.clients.accept(self.bs["socket"], on_request=self.response)

  # receber as mensagens recebidas do cliente e enviar ao servidor
  def response(self, code, alias, data, client_socket):
    data["client_socket"] = alias
    if self.ms["status"]:
      console.send(self.ms["socket"], code, data)
    elif self.ts["status"]:
      console.send(self.ts["socket"], code, data)
        
  # receber as mensagens do servidor e enviar ao cliente
  def receive(self, client_socket):
    while True:
      code, data = console.recv(client_socket)
      if code is None or data is None:
        continue
      if "client_socket" in data:
        console.send(self.clients.get(data["client_socket"]), code)

  # realiza tentativas de conexão com o servidor
  def attempt(self):
    connection.attempt(
      on_success=self.main_server_connect,
      on_stop=self.temp_server_connect,
      on_fail_msg="Não foi possível conectar ao servidor principal. Tentando novamente em 5 segundos.",
      case=not self.ms["status"] and not self.ts["status"],
      max_attempts=20,
      delay=5,
    )

  # conectar ao servidor principal
  def main_server_connect(self):
    self.ms["socket"].connect((self.ms["host"], self.ms["port"]))
    self.ms["status"] = True
    print("Conectado ao servidor principal")

    client = agent()
    client.interate(self.ms["socket"], on_send=self.receive)

    if self.ts["status"]:
      self.ts["status"] = False
      self.ts["socket"].close()

  # conectar ao servidor temporário
  def temp_server_connect(self):

    ts = server(database("src/database.sq3"))
    ts.init(TEMP_SERVER, message="Servidor temporário escutando em {}:{}")

    self.ts["socket"].connect((self.ts["host"], self.ts["port"]))
    self.ts["status"] = True
    print("Conectado ao servidor temporário")

    client = agent()
    client.interate(self.ts["socket"], on_send=self.receive)

    print("Não foi possível conectar ao servidor principal. Tentando novamente em 7 segundos.")
    server.reconnect(main_server=self.ms, on_success=self.main_server_connect, delay=7)

