import socket
import threading
import os
import sys
import json
from library import console, helper, _
from app import *
from datetime import date
from constants import consts

class receiver(app):
  
	LOGGED = False

	USERDATA = {}

	def login(self):
		while True:
			print(_("enter.username"))
			username = self.enter_username()
			print(_("enter.password"))
			password = input("> ")
			self.socket.send(json.dumps([consts.COM_LOGIN, [username, password]]).encode())
			codigo, data = json.loads(self.socket.recv(1024).decode())
			match codigo:
				case consts.ERROR:
					console.print_alerta(_("auth.fail"))
				case consts.SUCCESS:
					name, role = data["userdata"]
					self.LOGGED = True
					self.USERDATA = {
						"username": username,
						"password": password,
						"name": name,
						"role": role,
					}
					self.SERVER_BACKUP = data["server_backup"]
					self.INPUT_PREFIX = f"{console.OKGREEN}{username}@projetoa3{console.ENDC}: "
					console.print_sucesso(_("auth.success"))
					console.print_info(f"Bem vindo de volta {console.OKCYAN}{console.UNDERLINE}{name}{console.ENDC}{console.OKBLUE}!{console.ENDC}")
					break

	def response(self):
		while self.LOGGED:
			data = self.socket.recv(1024)
			data = json.loads(data.decode())
			match data[0]:
				case consts.COM_SIMULATE_CONNECTION_FAILURE:
					console.print_erro(_("connection.main.server.failed"))
					host, port = self.SERVER_BACKUP
					self.socket.close()
					# criar um novo objeto de soquete do servidor
					self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					# atualizar o endereço do servidor
					new_address = (host, int(port))
					print(_("connecting.new.server").format(host, port))
					self.socket.connect(new_address)
					console.print_sucesso(_("connected.backup.server"))
					# realizar novamente a autenticação com os dados já salvos
					self.socket.send(json.dumps([consts.COM_RECONNECT, [self.USERDATA["username"], self.USERDATA["password"]]]).encode())
					print(_("continue"))
					continue
				case consts.COM_EXIT:
					self.LOGGED = False
					break
				case consts.ERROR | consts.SUCCESS:
					continue
				case _:
					if len(data) < 3:
						print(data[1])

	def enter_price(self):
		value = None
		while True:
			value = input("> ")
			if helper.validate_price(value):
				break
			else:
				print(_("invalid.price"))
		return value

	def enter_username(self):
		value = None
		while True:
			value = input("> ").lower()
			if helper.validate_username(value):
				break
			else:
				print(_("invalid.username"))
		return value

	def enter_date(self):
		value = None
		while True:
			value = input("> ")
			if helper.validate_date(value):
				break
			else:
				print(_("invalid.date"))
		return value

	def request(self):
		while self.LOGGED:

			if not self.command_code():
				continue

			code = self.COMMAND_CODE
			data = {}

			if self.COMMAND_CODE == consts.COM_EXIT:
				self.socket.send(json.dumps(data).encode())
				break

			match self.USERDATA["role"]:
				case consts.MANAGER:
					match self.COMMAND_CODE:
						# total de vendas de um vendedor
						case consts.COM_SELLER_TOTAL_SALES:
							print(_("enter.seller.username"))
							data["username"] = self.enter_username()
						# total de vendas de uma loja
						case consts.COM_SHOP_TOTAL_SALES:
							print(_("enter.shopname"))
							data["name"] = input("> ").lower()
						# total de vendas da rede de lojas em um período
						case consts.COM_TOTAL_SALES_PERIOD:
							print(_("enter.date.min"))
							data["min"] = self.enter_date()
							print(_("enter.date.max"))
							data["max"] = self.enter_date()
						case _:
							if self.COMMAND_CODE not in [consts.COM_EXIT, consts.COM_BEST_SELLER, consts.COM_BEST_SHOP]:
								console.print_erro(_("command.unknown"))
								continue
				case consts.SELLER:
					match self.COMMAND_CODE:
						# adicionar venda
						case consts.COM_ADD_SALE:
							print(_("enter.shopname"))
							data["shopname"] = input("> ")
							print(_("enter.price"))
							data["price"] = self.enter_price()
							data["date"] = str(date.today())
						case _:
							console.print_erro(_("command.unknown"))
							continue

			self.socket.send(json.dumps([code, data]).encode())

	def start(self):
		if len(sys.argv) < 3:
			console.print_notificacao("client.py")
			return
		
		self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self.socket.connect((sys.argv[1], int(sys.argv[2])))
		
		console.intro()
		console.print_info(_("login.message"))

		self.login()

		userInputThread = threading.Thread(target=self.request)
		serverListenThread = threading.Thread(target=self.response)

		if self.LOGGED:
			console.print_comandos(self.USERDATA["role"])
			console.print_info(_("command.info"))
			userInputThread.start()
			serverListenThread.start()

		while True:
			if not self.LOGGED:
				self.socket.shutdown(socket.SHUT_RDWR)
				self.socket.close()
				console.print_sucesso(_("logout.message"))
				os._exit(1)

receiver = receiver()
receiver.start()