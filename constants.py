import types

consts = types.SimpleNamespace()
consts.TYPE_TEXT = 21
consts.TYPE_DATE = 22
consts.TYPE_CLIENT = 23
consts.TYPE_SERVER = 24

consts.TYPE_WARNING = 31
consts.TYPE_INFO = 32
consts.TYPE_SUCCESS = 33
consts.TYPE_DANGER = 34

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
consts.COM_LOGIN = 10

consts.ERROR = 0
consts.SUCCESS = 1