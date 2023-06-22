import sys
from src.utils import *

MAIN_SERVER = {
	"host": "localhost",
	"port": 8080,
	"status": False,
}

def ms_init():
  ms = server(database("src/database.sq3"))
  ms.init(MAIN_SERVER, message="Servidor principal escutando em {}:{}")

def mws_init():
  mws_server = middleware_server(MAIN_SERVER, TEMP_SERVER, MIDDLEWARE_SERVER)
  mws_server.start()
  
def main():
  state = sys.argv[1] if len(sys.argv) > 1 else ""

  # simulação com servidor principal desconectado e reconexão
  if state == '-f':
    mws_init()
    time.sleep(4)
    ms_init()
  else:
    ms_init()
    time.sleep(1)
    mws_init()

if __name__ == "__main__":
  main()