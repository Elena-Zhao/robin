import csv
from robinhood import Robinhood
from orderreader import OrderReader

rb = Robinhood()
rb.login(username="suhang3240", password="*Sqwer1234")
order_reader = OrderReader()
order_reader.init_robinhood_from_client(rb)

orders = order_reader.get_orders()

keys = ['side', 'symbol', 'shares', 'price', 'date', 'state']
with open('orders.csv', 'w') as output_file:
    dict_writer = csv.DictWriter(output_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(orders)
