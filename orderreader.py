import csv
import shelve
from datetime import datetime

class OrderReader:
  ''' OrderReader read orders either using a Robinhood client or use csv file '''

  def __init__(self):
    '''
    orders: list of orders
    sample order: {'side': 'buy', 'price': 10, 'shares': 30, 'symbol': 'DB', 'date': ..., 'state': 'filled'}
    '''
    self.orders = []


  def init_firstrade(self, csv_file):
    reader = csv.DictReader(open(csv_file))
    orders = []
    for line in reader:
      order = dict(line)
      if order['Transaction'] == 'Bought':
        side = 'buy'
        price = float(order['Price'])
      elif order['Transaction'] == 'Sold':
        side = 'sell'
        price = float(order['Price'])
      elif order['Transaction'] == 'Other':
        continue    # we don't process these now
        if order['Price'] == '':
          if order['Quantity'] == '':
            # this is an assigned fix
            continue
          #if order['Amount'] == '0':
            #continue
            # this is an account transfer, or fix like DB.RT or SCTY->TSLA
          # otherwise, this is a assigned stock
          price = float(order['Amount']) / float(order['Quantity'])
        if float(order['Quantity']) < 0:
          side = 'sell'
        else:
          side = 'buy'
      else:
        # we are leaving out 'Dividend', 'Deposit', 'Interest', 'Margin Interest', 'Withdraw'
        continue
      orders.append({
        'side': side,
        'price': price,
        'shares': abs(float(order['Quantity'])),
        'symbol': order['Symbol'],
        'date': datetime.strptime(order['Date'], '%m/%d/%Y'),
        'state': 'filled'})

    self.orders = sorted(orders, key=lambda k: k['date'])


  def init_robinhood_from_client(self, rb_client):
    past_orders = self.__get_all_history_orders(rb_client)
    instruments_db = shelve.open('instruments.db')
    orders = [self.__order_item_info(order, rb_client, instruments_db) for order in reversed(past_orders)]
    self.__fix_orders(orders)
    instruments_db.close()
    self.orders = orders


  def init_robinhood_from_csv(self, csv_file):
    reader = csv.DictReader(open(csv_file))
    orders = []
    for line in reader:
      order = dict(line)
      orders.append({
        'side': order['side'], 
        'price': float(order['price']),
        'shares': float(order['shares']),
        'symbol': order['symbol'],
        'date': datetime.strptime(order['date'], '%Y-%m-%d %H:%M:%S'),
        'state': order['state']})

    self.orders = sorted(orders, key=lambda k: k['date'])


  def __fix_orders(self, orders):
    orders2add = [{'side': 'buy', 'price': 0, 'shares': 30, 'symbol': 'DB^', 'date': datetime.strptime('2017-02-01', '%Y-%m-%d'), 'state': 'filled'}]
    for item in orders2add:
      for idx in range(len(orders)):
        if item['date'] < orders[idx]['date']:
          orders.insert(idx, item)
          break


  def __get_symbol_from_instrument_url(self, rb_client, url, db):
    instrument = {}
    if url in db:
      instrument = db[url]
    else:
      db[url] = self.__fetch_json_by_url(rb_client, url)
      instrument = db[url]
    return instrument['symbol']


  def __fetch_json_by_url(self, rb_client, url):
    return rb_client.session.get(url).json()


  def __order_item_info(self, order, rb_client, db):
    '''
    side: .side,  
    price: .average_price, 
    shares: .cumulative_quantity, 
    instrument: .instrument, 
    date : .last_transaction_at   "2017-06-20T15:47:05.468000Z"
    '''
    symbol = self.__get_symbol_from_instrument_url(rb_client, order['instrument'], db)
    if order['average_price'] is None:
      assert order['state'] != 'filled'
      order['average_price'] = '0'
    return {
        'side': order['side'],
        'price': float(order['average_price']),
        'shares': float(order['cumulative_quantity']),
        'symbol': symbol,
        'date': datetime.strptime(order['last_transaction_at'].split('.')[0], '%Y-%m-%dT%H:%M:%S'),
        'state': order['state']
    }


  def __get_all_history_orders(self, rb_client):
    orders = []
    past_orders = rb_client.order_history()
    orders.extend(past_orders['results'])
    while past_orders['next']:
      #print("{} order fetched".format(len(orders)))
      next_url = past_orders['next']
      past_orders = self.__fetch_json_by_url(rb_client, next_url)
      orders.extend(past_orders['results'])
    print("{} order fetched".format(len(orders)))
    return orders


  def get_orders(self):
    return self.orders
