import shelve
from datetime import datetime


def check_term(end_date, start_date):
  ''' check if this is a long term capital gain or short term'''

  one_year_date = datetime(year = start_date.year + 1, month = start_date.month, day = start_date.day)
  if end_date > one_year_date:
    return 'long'
  else: 
    return 'short'


class Positions:
  def __init__(self):
    '''
    sample position: { 'SCHW' : [ {'price': 42, 'shares' : 3, 'date': datetime.datetime(2017, 6, 20, 15, 47, 5, 468000)}, {}] }
    '''
    self.positions = {}


  def fill_buy_order(self, order):
    '''
    sample order: {'side': 'buy', 'price': 42.24000000, 'shares': 3.00000, 'symbol': 'SCHW', 'date': datetime.datetime(2017, 6, 20, 15, 47, 5, 468000), 'state': 'filled'}

    '''
    position_item = {'price': order['price'], 'shares': order['shares'], 'date': order['date']}

    if order['symbol'] in self.positions:
      self.positions[order['symbol']].append(position_item)
    else:
      self.positions[order['symbol']] = [position_item]


  def fill_sell_order(self, order, basis_method):
    assert basis_method == 'FIFO'   # we only support FIFO for the moment
    assert order['symbol'] in self.positions
    shares2sell = order['shares']
    realized = []
    while shares2sell > 0:
      position = self.positions[order['symbol']][0]
      if position['shares'] <= shares2sell:
        del self.positions[order['symbol']][0]
        shares_sold = position['shares']
        if len(self.positions[order['symbol']]) == 0:
          # no shares left for this symbol, we delete it
          del self.positions[order['symbol']]
      else:
        position['shares'] -= shares2sell
        shares_sold = shares2sell
      
      
      shares2sell -= shares_sold
      term = check_term(order['date'], position['date'])
      pnl = shares_sold * (order['price'] - position['price'])
      realized.append({'symbol': order['symbol'], 'date': order['date'], 'shares': shares_sold,
        'date': order['date'], 'term': term, 'price': order['price'], 'pnl': pnl})
    return realized

  def show(self):
    print("\tPrice\tShare\tDate")
    for symbol, positions in self.positions.items():
      print(symbol)
      for position in positions:
        print("\t%.2f\t%.2f\t%s" % (position['price'], position['shares'], position['date']))


class OrderLedger:

  def __init__(self, rb_client):
    self.basis_method = 'FIFO'    # 'FIFO' or 'LIFO'
    past_orders = self.__get_all_history_orders(rb_client)
    instruments_db = shelve.open('instruments.db')
    orders = [self.__order_item_info(order, rb_client, instruments_db) for order in reversed(past_orders)]
    self.__fix_orders(orders)
    instruments_db.close()

    self.orders = orders

    self.retrieve()

    self.position.show()


  def retrieve(self):

    self.position = Positions()
    self.realized = []

    for order in self.orders:
      if order['side'] == 'buy' and order['state'] == 'filled':
        self.position.fill_buy_order(order)
      elif order['side'] == 'sell' and order['state'] == 'filled':
        self.realized.extend(self.position.fill_sell_order(order, self.basis_method))


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
        'date': datetime.strptime(order['last_transaction_at'], '%Y-%m-%dT%H:%M:%S.%fZ'),
        'state': order['state']
    }


  def __get_all_history_orders(self, rb_client):
    orders = []
    past_orders = rb_client.order_history()
    orders.extend(past_orders['results'])
    while past_orders['next']:
#      print("{} order fetched".format(len(orders)))
      next_url = past_orders['next']
      past_orders = self.__fetch_json_by_url(rb_client, next_url)
      orders.extend(past_orders['results'])
    print("{} order fetched".format(len(orders)))
    return orders


  def get_all_orders(self):
    return self.orders

  def get_position():
    return self.position


  def get_period_pnl(self, start_date, end_date):
    '''
    start_date, end_date: datetime object
    '''
    return 1.0

  def get_last_year_pnl(self):
    start_date = datetime(year = datetime.today().year - 1, month = 1, day=1)
    end_date = datetime(year = datetime.today().year, month = 1, day=1)
    return self.get_period_pnl(start_date, end_date)

  def get_current_year_pnl(self):
    start_date = datetime(year = datetime.today().year, month = 1, day=1)
    end_date = datetime.now()
    return self.get_period_pnl(start_date, end_date)

  def get_unrealized_pnl(self):
    self.get_position()
    return 
