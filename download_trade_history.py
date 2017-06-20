import csv
from robinhood import Robinhood
from order_utils import *

rb = Robinhood()
rb.login(username="suhang3240", password="*Sqwer1234")
orders = get_all_order_details(rb)

keys = ['side', 'symbol', 'shares', 'price', 'date', 'state']
with open('orders.csv', 'w') as output_file:
    dict_writer = csv.DictWriter(output_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(orders)
