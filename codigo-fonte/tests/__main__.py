import unittest

def main():
  # descubrir e carregar todos os módulos de teste
  test_suite = unittest.defaultTestLoader.discover('tests/', pattern='*.py')
  # criar um TestRunner e executar os testes
  test_runner = unittest.TextTestRunner()
  test_runner.run(test_suite)

if __name__ == "__main__":
  main()