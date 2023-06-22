from typing import Callable
import socket
import threading
from src.library import *

MIDDLEWARE_SERVER = {
	"host": "localhost",
	"port": 8061,
	"status": False,
}

TEMP_SERVER = {
	"host": "localhost",
	"port": 8082,
	"status": False,
}

db = database("src/database.sq3")
db.connect()

class server():
  def __init__(self, database:database):
    self.db = database
    self.db.connect()
     
  def init(self, main_server, message):
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

  def on_client_connect(self, client_socket, alias:str):
      print(f"O cliente {alias} se conectou ao servidor")
      
  def resolve(self, code, alias, data, client_socket):
    s = self.clients.get(data["client_socket"])
    match code:
      case "/1":
        nome = data.get("username")
        if db.has_vendedor(nome):
          nome, vendas, total = db.get_total_vendas_vendedor(nome)
          console.send(s, "O vendedor {} realizou no total {} venda(s), totalizando R$ {:.2f}".format(nome,vendas,total), data)
        else: 
          console.send(s,"O vendedor '{}' não existe. Tente novamente.".format(nome), data)
      case "/2":
        nome = data.get("name")
        if db.has_loja(nome):
          vendas, total = db.get_total_vendas_loja(nome)
          console.send(s,"A loja {} teve no total {:d} venda(s), totalizando R$ {:.2f}".format(nome,vendas,total), data)
        else: 
          console.send(s,"A loja '{}' não existe. Tente novamente.".format(nome), data)
      case "/3":
        min = data.get("min")
        max = data.get("max")
        vendas, total = db.get_total_vendas_periodo(min, max)
        message = "O total de vendas da rede de lojas entre o periodo de {} e {} foi de {:d}, totalizando R$ {:.2f}".format(min,max,vendas,total)
        console.send(s,message, data)
      case "/4":
        nome, vendas, total = db.get_melhor_vendedor()
        message = "O melhor vendedor foi {} com o total de {:d} venda(s), totalizando R$ {:.2f}".format(nome,vendas,total)
        console.send(s,message, data)
      case "/5":
        nome, vendas, total = db.get_melhor_loja()
        message = "A melhor loja foi {} com o total de {:d} venda(s), totalizando R$ {:.2f}".format(nome,vendas,total)
        console.send(s,message, data)
      case "/7":
        userdata = data.get("userdata")
        price = data.get("price")
        shopname = data.get("shopname")
        db.add_sale(shopname, data.get("date"), price, userdata["id"])
        db.banco.commit()
        console.send(s,"Venda adicionada com sucesso!", data)
        self.clients.broadcast(data["client_socket"], f"O vendedor {userdata['name']} da loja {shopname} adicionou uma venda de {price}.")
      case _:
          console.send(s,"Comando desconhecido.", data)
      
  def reconnect(main_server, on_success:Callable, delay:int = 1):
    threading.Thread(target=connection.loop, args=(on_success,main_server, delay,)).start()

class client:

  code = None

  USERDATA = None

  def request(self, client_socket, auth):
    
    if auth:
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
         
      if self.code is not None:
        continue
      else:
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
        self.code = None
        if validate.is_command(code):
          self.code = code
          print("Digite o seu nome de usuário e senha para prosseguir.\n")
          print(f"O codigo ée: {code}\r")
          v = input("")
          console.send(client_socket, "/100", v)
        elif code:
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

class middleware_server:
    def __init__(self, main_server, temp_server, middleware_server):

        main_server["socket"] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        temp_server["socket"] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        middleware_server["socket"] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # main server client socket
        self.ms = main_server
        # temp server client socket
        self.ts = temp_server
        # middleware server client socket
        self.mws = middleware_server

    def start(self):
        host = self.mws["host"]
        port = self.mws["port"]

        connection.create_socket(self.mws["socket"], host, port)
        self.mws["status"] = True

        threading.Thread(target=self.run).start()
        threading.Thread(target=self.attempt).start()

    def run(self):
        self.clients = clients()
        self.clients.accept(
            self.mws["socket"], on_request=self.response
        )

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

    def attempt(self):
        connection.attempt(
            on_success=self.main_server_connect,
            on_stop=self.temp_server_connect,
            on_fail_msg="Não foi possível conectar ao servidor principal. Tentando novamente em 5 segundos.",
            case=not self.ms["status"] and not self.ts["status"],
            max_attempts=20,
            delay=5,
        )

    def main_server_connect(self):
        self.ms["socket"].connect((self.ms["host"], self.ms["port"]))
        self.ms["status"] = True
        print("Conectado ao servidor principal")

        client = agent()
        client.interate(self.ms["socket"], on_send=self.receive)

        if self.ts["status"]:
            self.ts["status"] = False
            self.ts["socket"].close()

    def temp_server_connect(self):

        ts = server(database("src/database.sq3"))
        ts.init(TEMP_SERVER, message="Servidor temporário escutando em {}:{}")

        self.ts["socket"].connect((self.ts["host"], self.ts["port"]))
        self.ts["status"] = True
        print("Conectado ao servidor temporário")

        client = agent()
        client.interate(self.ts["socket"], on_send=self.receive)

        print("Não foi possível conectar ao servidor principal. Tentando novamente em 7 segundos.")

        server.reconnect(
            main_server=self.ms, on_success=self.main_server_connect, delay=7
        )

        

    