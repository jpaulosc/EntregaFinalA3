import unittest
import socket
from context import *
from src.utils import MAIN_SERVER, MIDDLEWARE_SERVER
from src.library import connection

class TestConnectionMethods(unittest.TestCase):

  def test_ms_connection(self):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.assertTrue(connection.create_socket(server_socket, MAIN_SERVER['host'], MAIN_SERVER['port']))

  def test_mws_connection(self):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.assertTrue(connection.create_socket(server_socket, MIDDLEWARE_SERVER['host'], MIDDLEWARE_SERVER['port']))

if __name__ == '__main__':
  unittest.main()