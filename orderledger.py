from datetime import datetime


def check_term(end_date, start_date):
  ''' check if this is a long term capital gain or short term'''

  one_year_date = datetime(year = start_date.year + 1, month = start_date.month, day = start_date.day)
  if end_date > one_year_date:
    return 'long'
  else: 
    return 'short'


class Positions:
  '''
  record positions of the account
  use list of orders to initialize / maintain
  '''
  def __init__(self):
    '''
    sample position: { 'SCHW' : [ {'price': 42, 'shares' : 3, 
                                   'date': datetime.datetime(2017, 6, 20, 15, 47, 5, 468000)}, {}] }
    '''
    self.positions = {}


  def fill_buy_order(self, order, basis_method):
    '''
    sample order: {'side': 'buy', 'price': 42.24000000, 'shares': 3.00000, 'symbol': 'SCHW', 
                   'date': datetime.datetime(2017, 6, 20, 15, 47, 5, 468000), 'state': 'filled'}

    '''
    assert basis_method == 'FIFO'   # we only support FIFO for the moment
    shares2buy = order['shares']
    realized = []
    
    while shares2buy > 0 and order['symbol'] in self.positions:
      position = self.positions[order['symbol']][0]
      if position['shares'] > 0:
        # this is normal buying
        break
      if -position['shares'] > shares2buy:
        # not fully covered
        position['shares'] += shares2buy
        shares_bought = shares2buy
      else:
        # fully covered for this position, all gone
        del self.positions[order['symbol']][0]
        shares_bought = -position['shares']
        if len(self.positions[order['symbol']]) == 0:
          # all short positions are covered
          del self.positions[order['symbol']]
      shares2buy -= shares_bought
      term = check_term(order['date'], position['date'])
      pnl = shares_bought * (position['price'] - order['price'])
      realized.append({'symbol': order['symbol'], 'date': order['date'], 'shares': shares_bought,
        'term': term, 'price': order['price'], 'pnl': pnl, 'type': 'cover'})
    
    if shares2buy > 0:
      position_item = {'price': order['price'], 'shares': order['shares'], 'date': order['date']}
      positions = self.positions.get(order['symbol'], [])
      positions.append(position_item)
      self.positions[order['symbol']] = positions

    return realized


  def fill_sell_order(self, order, basis_method):
    assert basis_method == 'FIFO'   # we only support FIFO for the moment
    shares2sell = order['shares']
    realized = []
    while shares2sell > 0 and order['symbol'] in self.positions:
      position = self.positions[order['symbol']][0]
      if position['shares'] < 0:
        # we are short selling this symbol
        break
      if position['shares'] <= shares2sell:
        # not enough for selling, all gone for this position
        del self.positions[order['symbol']][0]
        shares_sold = position['shares']
        if len(self.positions[order['symbol']]) == 0:
          # no shares left for this symbol, we delete it
          del self.positions[order['symbol']]
      else:
        # we only sell part of this position
        position['shares'] -= shares2sell
        shares_sold = shares2sell
      
      shares2sell -= shares_sold
      term = check_term(order['date'], position['date'])
      pnl = shares_sold * (order['price'] - position['price'])
      realized.append({'symbol': order['symbol'], 'date': order['date'], 'shares': shares_sold,
        'term': term, 'price': order['price'], 'pnl': pnl, 'type': 'sell'})

    if shares2sell > 0:
      # we need to short this many shares
      position_item = {'price': order['price'], 'shares': -order['shares'], 'date': order['date']}
      positions = self.positions.get(order['symbol'], [])
      positions.append(position_item)
      self.positions[order['symbol']] = positions

    return realized


  def show(self):
    print("\tBasis\tShare\tDate")
    for symbol, positions in self.positions.items():
      print(symbol)
      for position in positions:
        print("\t%.2f\t%.2f\t%s" % (position['price'], position['shares'], position['date']))


  def get_unrealized(self, rb_client):
    unrealized = []
    for symbol, positions in self.positions.items():
      quote_price = float(rb_client.quote_data(symbol)['last_trade_price'])
      for position in positions:
        term = check_term(datetime.today(), position['date'])
        pnl = position['shares'] * (quote_price - position['price']) 
        unrealized.append({'symbol': symbol, 'date': datetime.today(), 'shares': position['shares'],
          'term': term, 'price': quote_price, 'pnl': pnl})
    return unrealized


class OrderLedger:
  ''' OrderLedger class used to maintain orders and perform analysis on orders'''

  def __init__(self, orders):
    self.basis_method = 'FIFO'    # 'FIFO' or 'LIFO'
    self.orders = orders
    self.retrieve()
  

  def retrieve(self):

    self.position = Positions()
    self.realized = []

    for order in self.orders:
      if order['side'] == 'buy' and order['state'] == 'filled':
        self.realized.extend(self.position.fill_buy_order(order, self.basis_method))
      elif order['side'] == 'sell' and order['state'] == 'filled':
        self.realized.extend(self.position.fill_sell_order(order, self.basis_method))


  def get_all_orders(self):
    return self.orders


  def get_period_pnl(self, start_date, end_date):
    '''
    start_date, end_date: datetime object
    '''
    period_realized = []
    for item in self.realized:
      if item['date'] <= end_date and item['date'] >= start_date:
        period_realized.append(item)

    self.show_pnl(period_realized)


  def get_last_year_pnl(self):
    start_date = datetime(year = datetime.today().year - 1, month = 1, day=1)
    end_date = datetime(year = datetime.today().year, month = 1, day=1)
    return self.get_period_pnl(start_date, end_date)


  def get_current_year_pnl(self):
    start_date = datetime(year = datetime.today().year, month = 1, day=1)
    end_date = datetime.now()
    return self.get_period_pnl(start_date, end_date)


  def get_unrealized_pnl(self, rb_client):
    unrealized = self.position.get_unrealized(rb_client)
    self.show_pnl(unrealized)


  def show_orders(self):
    print("Date\t\tSymbol\tSide\tShares\tPrice\tState")
    print("-------------------------------------------------------")
    for order in self.orders:
      print("%s\t%s\t%s\t%4d\t%.2f\t%s"%(order['date'].strftime("%Y-%m-%d"), order['symbol'], order['side'], order['shares'], order['price'], order['state']))


  def show_realized(self, realized):
    print("Date\t\tSymbol\tShares\tPrice\tTerm\t    PNL\t  Type")
    print("----------------------------------------------------------")
    for order in realized:
      print("%s\t%s\t%4d\t%6.2f\t%s%10.2f\t  %s"% (order['date'].strftime("%Y-%m-%d"), order['symbol'], order['shares'], order['price'], order['term'], order['pnl'], order['type']))


  def show_positions(self):
    self.position.show()


  def show_pnl(self, sales):
    sales_total = {}
    for sale in sales:
      symbol_total = sales_total.get(sale['symbol'],  {'pnl': 0, 'short': 0, 'long': 0})
      sale_short_pnl = sale['pnl'] if sale['term'] == 'short' else 0
      sale_long_pnl = sale['pnl'] if sale['term'] == 'long' else 0
      sales_total[sale['symbol']] = { 
          'pnl': symbol_total['pnl'] + sale['pnl'],
          'short': symbol_total['short'] + sale_short_pnl,
          'long': symbol_total['long'] + sale_long_pnl
          }

    print("Symbol\ttotal gain\tshort term\tlong term")
    print("--------------------------------------------------")
    total = {'pnl': 0, 'short': 0, 'long': 0}
    for symbol, info in sales_total.items():
      total['pnl'] += info['pnl']
      total['short'] += info['short']
      total['long'] += info['long']
      print("%s\t%10.2f\t%10.2f\t%9.2f" % (symbol, info['pnl'], info['short'], info['long']))

    print("--------------------------------------------------")
    print("%s\t%10.2f\t%10.2f\t%9.2f" % ("Total", total['pnl'], total['short'], total['long']))
    print("")
