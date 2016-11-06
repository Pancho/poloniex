import time


from poloniex import poloniex


def test_ticker():
	api = poloniex.Poloniex('examples/config.py')

	while True:
		print(api.ticker())
		# Change this to less at your own risk - Bitstamp has a harsh policy about exceeding allowed number of calls
		time.sleep(1)


def test_volume():
	api = poloniex.Poloniex('examples/config.py')

	while True:
		print(api.daily_volume())
		# Change this to less at your own risk - Bitstamp has a harsh policy about exceeding allowed number of calls
		time.sleep(1)


def test_order_book():
	api = poloniex.Poloniex('examples/config.py')

	while True:
		print(api.order_book())
		# Change this to less at your own risk - Bitstamp has a harsh policy about exceeding allowed number of calls
		time.sleep(1)


def test_ws(*args, **kwargs):
	print(args, kwargs)


if __name__ == '__main__':
	api = poloniex.Poloniex('examples/config.py')
	api.attach_order_book(test_ws, 'BTC_ETH')
