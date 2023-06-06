import socket
import json
from datetime import date
from lib import console

HOST = 'localhost'
PORT = 5000

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
enderecoServidor = (HOST, PORT)

try:
  s.connect(enderecoServidor)
  print("Conexão estabelecida com sucesso.")
except ConnectionRefusedError:
  print("A conexão foi recusada pelo servidor.")
  print("Inciando a conexão com o servidor de backup...")
  enderecoServidor = (HOST, 5001)
  s.connect(enderecoServidor)
except TimeoutError:
  print("Tempo limite de conexão excedido.")
except Exception as e:
  print("Ocorreu um erro durante a conexão:", str(e))

user = None
comandos = {
  "gerente": [
    "1 - Total de vendas de um vendedor",
    "2 - Total de vendas de uma loja",
    "3 - Total de vendas da rede de lojas em um período",
    "4 - Melhor vendedor",
    "5 - Melhor loja",
    "0 - Sair"
  ],
  "vendedor": [
    "1 - Adicionar venda",
    "0 - Sair"
  ]
}

console.intro()
console.print_info("Digite o seu nome de usuário e senha para prosseguir.")
print("\t")

# login
while True:
  # código de operação
  m = {"code": 7}
  print("Digite o nome de usuário:")
  m["username"] = input("> ")
  print("Digite a senha:")
  m["password"] = input("> ")

  s.sendto(json.dumps(m).encode(), enderecoServidor)
  resposta = s.recv(1024).decode()

  if resposta == "0":
    console.print_alerta("Usuário não existe ou senha incorreta. Tente novamente.")
  else :
    user = json.loads(resposta)
    cargo = user[2]
    print("\t")
    console.print_sucesso("Autenticação realizada com sucesso!")
    console.print_info(f"Bem vindo de volta {console.OKCYAN}{console.UNDERLINE}{user[1]}{console.ENDC}{console.OKBLUE}!{console.ENDC}")
    print("\t")
    print("Comandos disponíveis:")
    for comando in comandos[cargo]:
      print(comando)
    print("\t")
    print(console.OKBLUE + f"Digite o {console.BOLD}número do comando{console.ENDC} {console.OKBLUE}para realizar alguma tarefa." + console.ENDC)
    break

prefixo = f"{console.OKGREEN}{user[3]}@projetoa3{console.ENDC}"

while True:
  m = {"code": -1}
  # código de operação
  m["code"] = int(input(f"{prefixo}: "))

  cargo = user[2]

  match cargo:
    case "vendedor":
      match m["code"]:
        # adicionar venda
        case 1:
          print("Digite o nome da loja:")
          m["loja"] = input("> ")
          print("Digite o valor:")
          m["valor"] = float(input("> "))
          m["data"] = str(date.today())
          m["code"] = 6
        case _:
          if m["code"] != 0:
            console.print_erro("Código de comando inválido")
            continue
    case "gerente":
      match m["code"]:
        # total de vendas de um vendedor
        case 1:
          print("Digite o nome de usuário do vendedor:")
          m["username"] = input("> ")
        # total de vendas de uma loja
        case 2:
          print("Digite o nome da loja:")
          m["nome"] = input("> ")
        # total de vendas da rede de lojas em um período
        case 3:
          print("Digite a data minima(AAAA-MM-DD):")
          m["min"] = input("> ")
          print("Digite a data maxima(AAAA-MM-DD):")
          m["max"] = input("> ")
        case _:
          if m["code"] not in [0, 4, 5]:
            console.print_erro("Código de comando inválido")
            continue

  jsonData = json.dumps(m)
  s.sendto(jsonData.encode(), enderecoServidor)
  print(s.recv(1024).decode())

  if m["code"] == 0:
    print(s.recv(1024).decode())
    break
