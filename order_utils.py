import shelve
from datetime import datetime

def get_symbol_from_instrument_url(rb_client, url, db):
    instrument = {}
    if url in db:
        instrument = db[url]
    else:
        db[url] = fetch_json_by_url(rb_client, url)
        instrument = db[url]
    return instrument['symbol']


def fetch_json_by_url(rb_client, url):
    return rb_client.session.get(url).json()


def order_item_info(order, rb_client, db):
    '''
    side: .side,  
    price: .average_price, 
    shares: .cumulative_quantity, 
    instrument: .instrument, 
    date : .last_transaction_at   "2017-06-20T15:47:05.468000Z"
    '''
    symbol = get_symbol_from_instrument_url(rb_client, order['instrument'], db)
    return {
        'side': order['side'],
        'price': order['average_price'],
        'shares': order['cumulative_quantity'],
        'symbol': symbol,
        'date': datetime.strptime(order['last_transaction_at'], '%Y-%m-%dT%H:%M:%S.%fZ'),
        'state': order['state']
    }


def get_all_history_orders(rb_client):
    orders = []
    past_orders = rb_client.order_history()
    orders.extend(past_orders['results'])
    while past_orders['next']:
        print("{} order fetched".format(len(orders)))
        next_url = past_orders['next']
        past_orders = fetch_json_by_url(rb_client, next_url)
        orders.extend(past_orders['results'])
    print("{} order fetched".format(len(orders)))
    return orders


def get_all_order_details(rb_client):
  past_orders = get_all_history_orders(rb_client)
  instruments_db = shelve.open('instruments.db')
  orders = [order_item_info(order, rb_client, instruments_db) for order in past_orders]
  instruments_db.close()
  return orders

