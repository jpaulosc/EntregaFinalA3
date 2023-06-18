import socket
import threading
import os
import sys
import json
from lib import database, console
from datetime import date
import importlib

state = {"connected": False}
app_db = database("banco-de-dados.sq3")
server_backup = None

# Create a socket object
s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

def login():
	global s, server_backup
	while True:
		print("Digite o nome de usuário:")
		state["username"] = input("> ").lower()
		print("Digite a senha:")
		state["password"] = input("> ")
		state["logado"] = False
		s.send(json.dumps([state["username"], state["password"]]).encode())
		data = s.recv(1024).decode()
		match data:
			case "/wrongPasswordOrUsername":
				console.print_alerta("O nome de usuário ou a senha digitados estão incorretos. Tente novamente")
			case _:
				cargo, name, server_backup = json.loads(data)
				state["logado"] = True
				state["cargo"] = cargo
				server_backup = server_backup
				state["prefixo"] = f"{console.OKGREEN}{state['username']}@projetoa3{console.ENDC}"
				console.print_sucesso("\nAutenticação realizada com sucesso!\n")
				console.print_info(f"Bem vindo de volta {console.OKCYAN}{console.UNDERLINE}{name}{console.ENDC}{console.OKBLUE}!{console.ENDC}")
				break

def response():
	global s, state
	while state["logado"]:
		data = s.recv(1024)
		data = json.loads(data.decode())
		match data[0]:
			case 8:
				print("Falha de conexão com o servidor")
				host, port = server_backup
				s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				# Update the server address
				new_address = (host, int(port))
				print(f'Connecting to the new server at {new_address}')
				s.connect(new_address)
				print('Connected to the new server')
				s.send(json.dumps([state["username"], state["password"]]).encode())
				continue
			case 0:
				state["logado"] = False
				break
			case _:
				if len(data) < 3:
					print(data[1])

def request():
	while state["logado"]:

		codigo = input(f"{state['prefixo']}: ")
		if codigo.isdigit():
			codigo = int(codigo)
		else:
			print("Entrada inválida. Por favor insira um número válido.")
			continue

		m = {"codigo": codigo}

		if codigo == 0:
			s.send(json.dumps(m).encode())
			break

		match state["cargo"]:
			case "gerente":
				match codigo:
					# total de vendas de um vendedor
					case 1:
						print("Digite o nome de usuário do vendedor:")
						m["username"] = input("> ")
					# total de vendas de uma loja
					case 2:
						print("Digite o nome da loja:")
						m["nome"] = input("> ").lower()
					# total de vendas da rede de lojas em um período
					case 3:
						print("Digite a data minima(AAAA-MM-DD):")
						m["min"] = input("> ")
						print("Digite a data maxima(AAAA-MM-DD):")
						m["max"] = input("> ")
					case _:
						if codigo not in [0, 4, 5]:
							console.print_erro("Código de comando inválido")
							continue
			case "vendedor":
				match codigo:
					# adicionar venda
					case 1:
						print("Digite o nome da loja:")
						m["loja"] = input("> ")
						print("Digite o valor:")
						m["valor"] = float(input("> "))
						m["data"] = str(date.today())
						m["codigo"] = 6
					case _:
						console.print_erro("Código de comando inválido")
						continue

		s.send(json.dumps(m).encode())

def init():
	global s

	if len(sys.argv) < 3:
		console.print_notificacao("client.py")
		return
	
	s.connect((sys.argv[1], int(sys.argv[2])))
	
	console.intro()
	console.print_info("Digite o seu nome de usuário e senha para prosseguir.\n")

	login()

	userInputThread = threading.Thread(target=request)
	serverListenThread = threading.Thread(target=response)

	if state["logado"]:
		console.print_comandos(state["cargo"])
		print(console.OKBLUE + f"Digite o {console.BOLD}número do comando{console.ENDC} {console.OKBLUE}para realizar alguma tarefa.\n" + console.ENDC)
		userInputThread.start()
		serverListenThread.start()

	while True:
		if not state["logado"]:
			s.shutdown(socket.SHUT_RDWR)
			s.close()
			print("\nDesconectado do A3Projeto.")
			os._exit(1)

init()