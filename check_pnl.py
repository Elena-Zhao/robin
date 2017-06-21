from robinhood import Robinhood
from orderledger import OrderLedger

def print_pnl(pnls):
  '''
  '''
  print('-----------------------------------')
  print(pnls)



rb = Robinhood()
rb.login(username="suhang3240", password="*Sqwer1234")
ol = OrderLedger(rb)

pnls = {
    'last_year': ol.get_last_year_pnl(),
    'this_year': ol.get_current_year_pnl(),
    'unrealized': ol.get_unrealized_pnl()
    }

for period, pnls in pnls.items():
  print("%s PNL" % period)
  print_pnl(pnls)
