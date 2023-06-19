import socket
import threading
import os
import json
import sys
from library import database, console, helper
from constants import consts

class sender():
	
	SERVERS = []

	CLIENTS = []

	SERVER_BACKUP = None

	USERS = {}

	def backend(self):
		while True:
			codigo = input("")
			if codigo.isdigit():
				codigo = int(codigo)
			else:
				print("Entrada inválida. Por favor insira um número válido.")
				continue
				
			match codigo:
				case consts.COM_EXIT:
					for client in self.CLIENTS:
						client.send(json.dumps([codigo, None]).encode())
					os._exit(1) 
				case consts.COM_ACTIVE_CLIENTS:
					for client in self.CLIENTS:
						print(client.getsockname())
				case consts.COM_LOGGED_USERS:
					for username in self.USERS:
						user = self.USERS[username]
						print(f"{user['id']}, {user['username']}, {user['nome']}, {user['cargo']}")
				case consts.COM_SIMULATE_CONNECTION_FAILURE:
					print("Inciando a conexão com o servidor de backup...")
					self.connect_backup_server()
					print("Servidor de backup iniciado")
					for client in self.CLIENTS:
						client.send(json.dumps([codigo, None]).encode())
					self.initiliaze(self.SERVERS[1])
				case _:
					print("comando invalido")

	def frontend(self, s):
		while True:
			client, address = s.accept()
			print("Nova conexão em:", address)
			threading.Thread(target=self.connect, args=(client,address,)).start()
		
	def initiliaze(self, s):
		
		# Criar e iniciar dois threads para cada loop while
		thread1 = threading.Thread(target=self.backend)
		thread2 = threading.Thread(target=self.frontend,args=(s,))
		thread1.start()
		thread2.start()

		# Unir as threads para aguardar a conclusão
		thread1.join()
		thread2.join()

	def resolve(self, client, username:str):
		while True:
			try:
				json_data = client.recv(1024).decode()
			except ConnectionAbortedError:
				self.initiliaze(self.SERVERS[1])
				break

			try:
				data = json.loads(json_data) if json_data else {
					"codigo": consts.COM_EXIT
				}
			except json.JSONDecodeError as e:
				print("Error decoding JSON:", str(e))
				break
			
			codigo = data.get("codigo")
			match codigo:
				case consts.COM_EXIT:
					client.send(json.dumps([codigo, None]).encode())
					print(f"Usuário deslogado: {console.OKBLUE}{username}{console.ENDC}")
					del self.USERS[username]
					break
				case consts.COM_SELLER_TOTAL_SALES:
					nome = data.get("username")
					if self.database.has_vendedor(nome):
						nome, vendas, total = self.database.get_total_vendas_vendedor(nome)
						client.send(json.dumps([codigo, f"O vendedor {nome} realizou no total {int(vendas)} venda(s), totalizando R$ {float(total)}"]).encode())
					else: 
						client.send(json.dumps([codigo, f"O vendedor '{nome}' não existe. Tente novamente.".encode()]).encode())
				case consts.COM_SHOP_TOTAL_SALES:
					nome = data.get("nome")
					if self.database.has_loja(nome):
						vendas, total = self.database.get_total_vendas_loja(nome)
						client.send(json.dumps([codigo, f"A loja {nome} teve no total {int(vendas)} venda(s), totalizando R$ {float(total)}"]).encode())
					else: 
						client.send(json.dumps([codigo, f"A loja '{nome}' não existe. Tente novamente."]).encode())
				case consts.COM_TOTAL_SALES_PERIOD:
					min = data.get("min")
					max = data.get("max")
					vendas, total = self.database.get_total_vendas_periodo(data.get("min"), data.get("max"))
					client.send(json.dumps([codigo, f"O total de vendas da rede de lojas entre o periodo de {min} e {max} foi de {int(vendas)}, totalizando R$ {float(total)}"]).encode())
				case consts.COM_BEST_SELLER:
					nome, vendas, total = self.database.get_melhor_vendedor()
					client.send(json.dumps([codigo, console.sprint_thebest('O melhor vendedor foi', nome, vendas, total)]).encode())
				case consts.COM_BEST_SHOP:
					nome, vendas, total = self.database.get_melhor_loja()
					client.send(json.dumps([codigo, console.sprint_thebest('A melhor loja foi', nome, vendas, total)]).encode())
				case consts.COM_ADD_SALE:
					self.database.add_venda(data.get("loja"), data.get("data"), data.get("valor"))
					client.send(json.dumps([codigo, "Dados inseridos com sucesso!"]).encode())
				case _:
					console.print_erro("Código de comando inválido")

	def connect(self, client, address:list):
		
		while True:
			data = client.recv(1024).decode()
			username, password = json.loads(data)

			# checar se o usuario ja esta logado.
			if username in self.USERS:
				print("Tentativa de conexão com um usuario já logado.")
			else:
				host, port = address
				userdata = self.database.login(username,password, host, port)
				if userdata is not None:
					id, nome, cargo = userdata

					if username not in self.USERS:
						self.CLIENTS.append(client)

					self.USERS[username] = {
						"id": id, 
						"username": username, 
						"nome": nome, 
						"cargo": cargo
					}

					threading.Thread(target=self.resolve, args=(client, username)).start()
					client.send(json.dumps([cargo, nome, self.SERVER_BACKUP]).encode())

					print(f"Uma nova conexão foi estabelecida no endereço {host}, na porta {port}")
					print(f"Novo usuário logado: {console.OKBLUE}{username}{console.ENDC}, seu cargo é {cargo}.")
					break
				else:
					client.send(b"/wrongPasswordOrUsername")

	def connect_backup_server(self):
		host, port = self.SERVER_BACKUP
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.bind((host, int(port)))
		s.listen(10)
		self.SERVERS.append(s)

	def start(self):
		if len(sys.argv) < 3:
			console.print_notificacao("server.py")
			return

		self.database = database("banco-de-dados.sq3")
		self.database.connect()
		self.database.clear()
		self.database.bulk_insert()
		
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.bind((sys.argv[1], int(sys.argv[2])))
		s.listen(10)

		self.SERVERS.append(s)
		self.SERVER_BACKUP = f"localhost {helper.get_random_open_port()}".split()

		console.print_comandos("admin")
		self.initiliaze(s)
	
sender = sender()
sender.start()