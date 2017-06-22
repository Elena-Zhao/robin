from robinhood import Robinhood
from orderledger import OrderLedger
from orderreader import OrderReader

def print_pnl(pnls):
  '''
  '''
  print('-----------------------------------')
  print(pnls)


rb = Robinhood()
rb.login(username="suhang3240", password="*Sqwer1234")
order_reader = OrderReader()
order_reader.init_firstrade('firstrade.csv')
#order_reader.init_robinhood_from_client(rb)
#order_reader.init_robinhood_from_csv('orders.csv')
ol = OrderLedger(order_reader.get_orders())

print("last year")
ol.get_last_year_pnl()

print("current year")
ol.get_current_year_pnl()

print("unrealized")
ol.get_unrealized_pnl(rb)

print("positions")
ol.show_positions()
