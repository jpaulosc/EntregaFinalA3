# A3Projeto Python

É um projeto simples e contém dois scripts python server.py que lidam com a solicitação do cliente e o client.py envia a solicitação e recebe a resposta do servidor por meio da comunicação do soquete.

## Pré-requisitos

Para executar o script python, seu sistema deve ter os seguintes programas/pacotes instalados
* Python 3.8

## Abordagem
* server.py necessário para executar no terminal.
* client.py necessário para executar a partir da máquina cliente e inserir o nome do host ou endereço IP.
* o servidor estabelecerá conexão entre o servidor e o cliente através do soquete.
* agora a partir do servidor ou texto do cliente pode ser enviado.

## Instruções (Servidor)
  
1. Abra uma janela de terminal no diretório que contém *server.py* e execute o seguinte comando:
> python server.py localhost 8000

2. Opcional. Substitua `localhost` pelo seu IP e `8000` por um número de porta TCP de sua escolha.

## Instruções (Cliente)

1. Abra uma janela de terminal no diretório que contém *client.py* e execute o seguinte comando:
> cliente python.py localhost 8000

2. Opcional. Substitua `localhost` pelo seu IP e `8000` por um número de porta TCP de sua escolha.

3. Um prompt para inserir o nome de usuário será exibido. Digite um nome de usuário e pressione enter.

4. Em seguida, aparecerá um prompt para inserir a senha. Digite a senha e pressione enter.

## Usuários cadastrados

Os seguintes usuários já estão cadastrados:

| Nome de usuário | Senha | Cargo |
|---|---|---|
| jess | 123 | gerente |
| carl | 123 | vendedor |
| paul | 123 | vendedor |
