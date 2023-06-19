import types

consts = types.SimpleNamespace()
consts.TYPE_TEXT = 10
consts.TYPE_DATE = 20
consts.TYPE_CLIENT = 30
consts.TYPE_SERVER = 40

consts.COM_EXIT = 0
# total de vendas de um vendedor
consts.COM_SELLER_TOTAL_SALES = 1
# total de vendas de uma loja
consts.COM_SHOP_TOTAL_SALES = 2
# total de vendas da rede de lojas em um período
consts.COM_TOTAL_SALES_PERIOD = 3
consts.COM_BEST_SELLER = 4
consts.COM_BEST_SHOP = 5
consts.COM_ADD_SALE = 6

consts.COM_ACTIVE_CLIENTS = 7
consts.COM_LOGGED_USERS = 8
consts.COM_SIMULATE_CONNECTION_FAILURE = 9

consts.ERROR = 0
consts.SUCCESS = 1