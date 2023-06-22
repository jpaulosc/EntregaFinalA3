import unittest
from context import *
from src.library import database

db = database("database.sq3")
db.connect()

def is_integer(n):
  return isinstance(n, int)

class TestDatabaseMethods(unittest.TestCase):

  def test_auth(self):
    self.assertIsNotNone(db.login('jess', '123'))
    self.assertIsNotNone(db.login('carl', '123'))
    self.assertIsNotNone(db.login('paul', '123'))

  def test_user(self):
    self.assertTrue(is_integer(db.get_userid('carl')))
    self.assertTrue(is_integer(db.get_userid('paul')))

  def test_sales(self):
    self.assertTrue(db.add_sale('americanas', '2023-04-12', 200, db.get_userid('carl')))
    self.assertTrue(db.add_sale('americanas', '2023-06-10', 410, db.get_userid('paul')))
    self.assertIsNotNone(db.get_total_vendas_periodo('2023-04-12','2023-06-15'))

  def test_hastable(self):
    self.assertTrue(db.has_table('users'))

  def test_hasstore(self):
    self.assertTrue(db.has_loja('bompreco'))
    self.assertTrue(db.has_loja('americanas'))

  def test_hasseller(self):
    self.assertTrue(db.has_vendedor('carl'))
    self.assertTrue(db.has_vendedor('paul'))

if __name__ == '__main__':
  unittest.main()