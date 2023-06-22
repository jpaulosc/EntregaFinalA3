import unittest
import socket
from context import *
from server.__main__ import MAIN_SERVER
from src.core import BRIDGE_SERVER
from src.library import connection

class TestConnectionMethods(unittest.TestCase):

  def test_ms_connection(self):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.assertTrue(connection.create_socket(server_socket, MAIN_SERVER['host'], MAIN_SERVER['port']))

  def test_mws_connection(self):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.assertTrue(connection.create_socket(server_socket, BRIDGE_SERVER['host'], BRIDGE_SERVER['port']))

if __name__ == '__main__':
  unittest.main()