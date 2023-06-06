from lib import servidor

# servidor de backup
s = servidor(host='localhost', port=5001, db='banco-de-dados.sq3')
s.iniciar()