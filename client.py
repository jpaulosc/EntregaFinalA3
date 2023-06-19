import socket
import threading
import os
import sys
import json
from library import console, app
from datetime import date
from constants import consts

class receiver(app):
  
	LOGGED = False

	USERDATA = {}

	def login(self):
		while True:
			print("Digite o nome de usuário:")
			username = input("> ").lower()
			print("Digite a senha:")
			password = input("> ")
			self.socket.send(json.dumps([consts.COM_LOGIN, [username, password]]).encode())
			codigo, data = json.loads(self.socket.recv(1024).decode())
			match codigo:
				case consts.ERROR:
					console.print_alerta("O nome de usuário ou a senha digitados estão incorretos. Tente novamente")
				case consts.SUCCESS:
					nome, cargo = data["userdata"]
					self.LOGGED = True
					self.USERDATA = {
						"username": username,
						"password": password,
						"nome": nome,
						"cargo": cargo,
					}
					self.SERVER_BACKUP = data["server_backup"]
					self.INPUT_PREFIX = f"{console.OKGREEN}{username}@projetoa3{console.ENDC}: "
					console.print_sucesso("\nAutenticação realizada com sucesso!\n")
					console.print_info(f"Bem vindo de volta {console.OKCYAN}{console.UNDERLINE}{nome}{console.ENDC}{console.OKBLUE}!{console.ENDC}")
					break

	def response(self):
		while self.LOGGED:
			data = self.socket.recv(1024)
			data = json.loads(data.decode())
			match data[0]:
				case consts.COM_SIMULATE_CONNECTION_FAILURE:
					console.print_alerta("Falha de conexão com o servidor principal.")
					host, port = self.SERVER_BACKUP
					self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					# Atualize o endereço do servidor
					novo_endereco = (host, int(port))
					print(f'Conectando-se ao novo servidor em {novo_endereco}...')
					self.socket.connect(novo_endereco)
					console.print_sucesso('Conectado ao servidor de backup.')
					# Realizar a autenticação com os dados já salvos
					self.socket.send(json.dumps([consts.COM_LOGIN, [self.USERDATA["username"], self.USERDATA["password"]]]).encode())
					print('Digite algum código de comando para continuar...')
					continue
				case consts.COM_EXIT:
					self.LOGGED = False
					break
				case consts.ERROR | consts.SUCCESS:
					continue
				case _:
					if len(data) < 3:
						print(data[1])

	def request(self):
		while self.LOGGED:

			if not self.command_code():
				continue

			m = {"codigo": self.COMMAND_CODE}

			if self.COMMAND_CODE == consts.COM_EXIT:
				self.socket.send(json.dumps(m).encode())
				break

			match self.USERDATA["cargo"]:
				case "gerente":
					match self.COMMAND_CODE:
						# total de vendas de um vendedor
						case consts.COM_SELLER_TOTAL_SALES:
							print("Digite o nome de usuário do vendedor:")
							m["username"] = input("> ")
						# total de vendas de uma loja
						case consts.COM_SHOP_TOTAL_SALES:
							print("Digite o nome da loja:")
							m["nome"] = input("> ").lower()
						# total de vendas da rede de lojas em um período
						case consts.COM_TOTAL_SALES_PERIOD:
							print("Digite a data minima(AAAA-MM-DD):")
							m["min"] = input("> ")
							print("Digite a data maxima(AAAA-MM-DD):")
							m["max"] = input("> ")
						case _:
							if self.COMMAND_CODE not in [consts.COM_EXIT, consts.COM_BEST_SELLER, consts.COM_BEST_SHOP]:
								console.print_erro("Código de comando inválido.")
								continue
				case "vendedor":
					match self.COMMAND_CODE:
						# adicionar venda
						case 1:
							print("Digite o nome da loja:")
							m["loja"] = input("> ")
							print("Digite o valor:")
							m["valor"] = float(input("> "))
							m["data"] = str(date.today())
							m["codigo"] = consts.COM_ADD_SALE
						case _:
							console.print_erro("Código de comando inválido.")
							continue

			self.socket.send(json.dumps(m).encode())

	def start(self):
		if len(sys.argv) < 3:
			console.print_notificacao("client.py")
			return
		
		self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self.socket.connect((sys.argv[1], int(sys.argv[2])))
		
		console.intro()
		console.print_info("Digite o seu nome de usuário e senha para prosseguir.\n")

		self.login()

		userInputThread = threading.Thread(target=self.request)
		serverListenThread = threading.Thread(target=self.response)

		if self.LOGGED:
			console.print_comandos(self.USERDATA["cargo"])
			print(console.OKBLUE + f"Digite o {console.BOLD}número do comando{console.ENDC} {console.OKBLUE}para realizar alguma tarefa.\n" + console.ENDC)
			userInputThread.start()
			serverListenThread.start()

		while True:
			if not self.LOGGED:
				self.socket.shutdown(socket.SHUT_RDWR)
				self.socket.close()
				console.print_sucesso("\nDesconectado do A3Projeto.")
				os._exit(1)

receiver = receiver()
receiver.start()