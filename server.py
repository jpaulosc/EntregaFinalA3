import socket
import threading
import os
import json
import sys
from library import database, console, helper, _
from app import app
from constants import consts

class sender(app):
	
	SERVERS = []

	CLIENTS = []

	USERS = {}

	def backend(self):
		while True:
			
			if not self.command_code():
				continue
				
			match self.COMMAND_CODE:
				case consts.COM_EXIT:
					try:
						for client in self.CLIENTS:
							client.send(json.dumps([self.COMMAND_CODE, None]).encode())
					finally:
						os._exit(1) 
				case consts.COM_ACTIVE_CLIENTS:
					for client in self.CLIENTS:
						print(client.getsockname())
				case consts.COM_LOGGED_USERS:
					for username in self.USERS:
						user = self.USERS[username]
						print(f"{user['id']}, {user['username']}, {user['name']}, {user['role']}")
				case consts.COM_SIMULATE_CONNECTION_FAILURE:
					print(_("initiating.connection.backup.server"))
					self.connect_backup_server()
					console.print_sucesso(_("backup.server.started"))
					for client in self.CLIENTS:
						client.send(json.dumps([self.COMMAND_CODE, None]).encode())
					self.initiliaze(self.SERVERS[1])
				case _:
					console.print_erro(_("command.unknown"))

	def frontend(self, s):
		while True:
			# permitir a conexão com o cliente
			client, [host, port] = s.accept()
			console.print_info(_("client.connection.established").format(host, port))

			# criar uma nova instância de Thread
			thread = threading.Thread(target=self.connect, args=(client,host,port,))
			# iniciar a execução da thread
			thread.start()
		
	def initiliaze(self, s):
		# criar e iniciar dois threads para o backend e frontend
		thread1 = threading.Thread(target=self.backend)
		thread2 = threading.Thread(target=self.frontend,args=(s,))
		# iniciar a execução das threads
		thread1.start()
		thread2.start()
		# aguardar a conclusão das threads
		thread1.join()
		thread2.join()

	def resolve(self, client, username:str):
		while True:
			try:
				json_data = client.recv(1024).decode()
			except ConnectionResetError:
				host, port = client.getsockname()
				console.print_erro(_("lost.connection").format(host, port))
				break
			except ConnectionAbortedError:
				self.initiliaze(self.SERVERS[1])
				break

			code, data = json.loads(json_data) if json_data else [consts.COM_BREAK, None]
			
			match code:
				case consts.COM_BREAK:
					del self.USERS[username]
					break
				case consts.COM_EXIT:
					client.send(json.dumps([code, None]).encode())
					print(_("user.disconnected").format(username))
					del self.USERS[username]
					break
				case consts.COM_SELLER_TOTAL_SALES:
					name = data.get("username")
					if self.database.has_vendedor(name):
						name, vendas, total = self.database.get_total_vendas_vendedor(name)
						client.send(json.dumps([code, _("msg.seller.total.sales").format(name, int(vendas), float(total))]).encode())
					else: 
						client.send(json.dumps([code, _("msg.unknown.seller").format(name)]).encode())
				case consts.COM_SHOP_TOTAL_SALES:
					name = data.get("name")
					if self.database.has_loja(name):
						vendas, total = self.database.get_total_vendas_loja(name)
						client.send(json.dumps([code, _("msg.shop.total.sales").format(name, int(vendas), float(total))]).encode())
					else: 
						client.send(json.dumps([code, _("msg.unknown.shop").format(name)]).encode())
				case consts.COM_TOTAL_SALES_PERIOD:
					min = data.get("min")
					max = data.get("max")
					vendas, total = self.database.get_total_vendas_periodo(data.get("min"), data.get("max"))
					if total is None:
						client.send(json.dumps([code, _("msg.nosales")]).encode())
					else:
						client.send(json.dumps([code, _("msg.total.sales.period").format(min, max, int(vendas), float(total))]).encode())
				case consts.COM_BEST_SELLER:
					name, vendas, total = self.database.get_melhor_vendedor()
					client.send(json.dumps([code, _("msg.best.seller").format(name, vendas, total)]).encode())
				case consts.COM_BEST_SHOP:
					name, vendas, total = self.database.get_melhor_loja()
					client.send(json.dumps([code, _("msg.best.shop").format(name, vendas, total)]).encode())
				case consts.COM_ADD_SALE:
					self.database.add_sale(data.get("shopname"), data.get("date"), data.get("price"), self.USERS[username]["id"])
					client.send(json.dumps([code, _("msg.data.entered")]).encode())
				case _:
					console.print_erro(_("command.unknown"))

	def connect(self, client, host:str, port):
		while True:
			try:
				codigo, data = json.loads(client.recv(1024).decode())
			except ConnectionResetError:
				console.print_erro(_("lost.connection").format(host, port))
				break
			
			match codigo:
				case consts.COM_LOGIN | consts.COM_RECONNECT:
					username, password = data
					# checar se o usuario ja esta logado.
					if username in self.USERS:
						console.print_alerta(_("auth.attempt"))
					else:
						userdata = self.database.login(username,password)
						if userdata is not None:
							id, name, role = userdata

							if username not in self.USERS:
								self.CLIENTS.append(client)

							self.USERS[username] = {
								"id": id, 
								"username": username, 
								"name": name, 
								"role": role
							}

							threading.Thread(target=self.resolve, args=(client, username)).start()
							client.send(json.dumps([consts.SUCCESS, {
								"server_backup": self.SERVER_BACKUP,
								"userdata": [name, role]
							}]).encode())
							print(_("user.connected" if codigo == consts.COM_LOGIN else "user.reconnected").format(username))
							break
						else:
							client.send(json.dumps([consts.ERROR, None]).encode())

	def connect_backup_server(self):
		host, port = self.SERVER_BACKUP
		# criar um objeto de soquete do servidor
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.bind((host, int(port)))
		s.listen(5)
		self.SERVERS.append(s)

	def create_file(self, filename:str) -> bool :
		if not os.path.exists(filename):
			with open(filename, 'w') as file:
				file.write("")
				return True
		return False

	def start(self):
		if len(sys.argv) < 3:
			console.print_notificacao("server.py")
			return

		db_file = "banco-de-dados.sq3"
		# criar arquivo, caso ele não exista
		self.create_file(db_file)
		self.database = database(db_file)
		self.database.connect()
		self.database.clear()
		self.database.bulk_insert()

		host = sys.argv[1]
		port = int(sys.argv[2])

		# criar um objeto de soquete do servidor
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			# vincular o objeto de soquete do servidor a um endereço e porta
			s.bind((host, port))
			# permitir no máximo 5 conexões em fila
			s.listen(5)
		except OSError:
			console.print_erro(_("address.use").format(host, port))
			return

		self.SERVERS.append(s)
		self.SERVER_BACKUP = f"localhost {helper.get_random_open_port()}".split()

		console.print_comandos("admin")

		print(_("waiting.connection"))
		self.initiliaze(s)
	
sender = sender()
sender.start()