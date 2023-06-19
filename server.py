import socket
import threading
import os
import json
import sys
from library import database, console, helper
from constants import consts

app_db = database("banco-de-dados.sq3")
logged_users = {}
servers = []
server_backup = None

def while_loop1():
	global logged_users
	while True:
		codigo = input("")
		if codigo.isdigit():
			codigo = int(codigo)
		else:
			print("Entrada inválida. Por favor insira um número válido.")
			continue
			
		match codigo:
			# Encerrar
			case consts.COM_EXIT:
				for username in logged_users:
					client = logged_users[username]['client']
					client.send(json.dumps([codigo, None]).encode())
				#	s.close()
				os._exit(1) 
			# Clientes ativos
			case consts.COM_ACTIVE_CLIENTS:
				for username in logged_users:
					client = logged_users[username]['client']
					print(client.getsockname())
			# 2 - Usuarios logados
			case consts.COM_LOGGED_USERS:
				for username in logged_users:
					user = logged_users[username]
					print(f"{user['id']}, {user['username']}, {user['nome']}, {user['cargo']}")
			case consts.COM_SIMULATE_CONNECTION_FAILURE:
				print("Inciando a conexão com o servidor de backup...")
				host, port = server_backup
				n = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				n.bind((host, int(port)))
				n.listen(10)
				servers.append(n)

				for username in logged_users:
					client = logged_users[username]['client']
					client.send(json.dumps([codigo, None]).encode())

				init_server(servers[1])
				print(3)
			case _:
				print("comando invalido")

def while_loop2(s):
	while True:
		client, address = s.accept()
		print("Nova conexão em:", address)
		threading.Thread(target=connect, args=(client,address,)).start()
	
def init_server(s):
	# Criar e iniciar dois threads para cada loop while
	thread1 = threading.Thread(target=while_loop1)
	thread2 = threading.Thread(target=while_loop2,args=(s,))
	thread1.start()
	thread2.start()

	# Unir as threads para aguardar a conclusão
	thread1.join()
	thread2.join()

def resolve(client, username):
	while True:
		try:
			json_data = client.recv(1024).decode()
		except ConnectionAbortedError:
			init_server(servers[1])
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
				del logged_users[username]
				break
			case consts.COM_SELLER_TOTAL_SALES:
				nome = data.get("username")
				if app_db.has_vendedor(nome):
					nome, vendas, total = app_db.get_total_vendas_vendedor(nome)
					client.send(json.dumps([codigo, f"O vendedor {nome} realizou no total {int(vendas)} venda(s), totalizando R$ {float(total)}"]).encode())
				else: 
					client.send(json.dumps([codigo, f"O vendedor '{nome}' não existe. Tente novamente.".encode()]).encode())
			case consts.COM_SHOP_TOTAL_SALES:
				nome = data.get("nome")
				if app_db.has_loja(nome):
					vendas, total = app_db.get_total_vendas_loja(nome)
					client.send(json.dumps([codigo, f"A loja {nome} teve no total {int(vendas)} venda(s), totalizando R$ {float(total)}"]).encode())
				else: 
					client.send(json.dumps([codigo, f"A loja '{nome}' não existe. Tente novamente."]).encode())
			case consts.COM_TOTAL_SALES_PERIOD:
				min = data.get("min")
				max = data.get("max")
				vendas, total = app_db.get_total_vendas_periodo(data.get("min"), data.get("max"))
				client.send(json.dumps([codigo, f"O total de vendas da rede de lojas entre o periodo de {min} e {max} foi de {int(vendas)}, totalizando R$ {float(total)}"]).encode())
			case consts.COM_BEST_SELLER:
				nome, vendas, total = app_db.get_melhor_vendedor()
				client.send(json.dumps([codigo, console.sprint_thebest('O melhor vendedor foi', nome, vendas, total)]).encode())
			case consts.COM_BEST_SHOP:
				nome, vendas, total = app_db.get_melhor_loja()
				client.send(json.dumps([codigo, console.sprint_thebest('A melhor loja foi', nome, vendas, total)]).encode())
			case consts.COM_ADD_SALE:
				app_db.add_venda(data.get("loja"), data.get("data"), data.get("valor"))
				client.send(json.dumps([codigo, "Dados inseridos com sucesso!"]).encode())
			case _:
				console.print_erro("Código de comando inválido")

def connect(client,address):
	
	while True:
		data = client.recv(1024).decode()
		username, password = json.loads(data)

		# checar se o usuario ja esta logado.
		if username in logged_users:
			print("Tentativa de conexão com um usuario já logado.")
		else:
			host, port = address
			userdata = app_db.login(username,password, host, port)
			if userdata is not None:
				id, nome, cargo = userdata
				logged_users[username] = {
					"id": id, 
					"client": client, 
					"username": username, 
					"nome": nome, 
					"cargo": cargo
				}

				threading.Thread(target=resolve, args=(client, username)).start()
				client.send(json.dumps([cargo, nome, server_backup]).encode())

				print(f"Uma nova conexão foi estabelecida no endereço {host}, na porta {port}")
				print(f"Novo usuário logado: {console.OKBLUE}{username}{console.ENDC}, seu cargo é {cargo}.")
				break
			else:
				client.send(b"/wrongPasswordOrUsername")

def init():
	global server_backup
	if len(sys.argv) < 3:
		console.print_notificacao("server.py")
		return

	app_db.connect()
	app_db.clear()
	app_db.bulk_insert()
	
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((sys.argv[1], int(sys.argv[2])))
	s.listen(10)

	servers.append(s)
	server_backup = f"localhost {helper.get_random_open_port()}".split()

	console.print_comandos("admin")
	init_server(s)

init()