import json
import decimal
import datetime
import hmac
import hashlib
import time
import urllib.parse
from configparser import ConfigParser


import requests
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner


EXAMPLES_URL = 'https://github.com/Pancho/poloniex'
CANDLE_PERIOD_300 = 300
CANDLE_PERIOD_900 = 900
CANDLE_PERIOD_1800 = 1800
CANDLE_PERIOD_7200 = 7200
CANDLE_PERIOD_14400 = 14400
CANDLE_PERIOD_86400 = 86400
CANDLE_PERIODS = [
	CANDLE_PERIOD_300,
	CANDLE_PERIOD_900,
	CANDLE_PERIOD_1800,
	CANDLE_PERIOD_7200,
	CANDLE_PERIOD_14400,
	CANDLE_PERIOD_86400,
]



class Poloniex(object):
	def __init__(self, config_file_path=None, api_key=None, secret=None):
		'''
		Constructor. You can instantiate this class with either file path or with all three values that would otherwise
		 be found in the config file.
		:param config_file_path: path to the file with the config
		:param api_key: API key found on https://www.poloniex.com/apiKeys/
		:param secret: Secret found on https://www.poloniex.com/apiKeys/ (disappears after some time)
		:return: The client object
		'''
		# None of the parameters are necessary, but to work properly, we need at least one pair from one source
		if config_file_path is None and (api_key is None or secret is None):
			raise Exception(
				'You need to pass either config_file_path parameter or all of api_key and secret')

		if config_file_path is not None:
			self.api_key, self.secret = self.__get_credentials(config_file_path)
		else:
			self.api_key = api_key
			self.secret = secret

		# Rather do it once instead of at every signing
		self.secret = self.secret.encode('utf8')

		# If still not api key and no secret, raise
		if self.api_key is None or self.api_key.strip() == '' or self.secret is None or self.secret.strip() == '':
			raise Exception('No credentials were found')

		self.api_endpoint = 'https://api.poloniex.com/'
		self.private_api_endpoint = 'https://www.poloniex.com/'

		# Init the runner to None
		self.runner = None
		self.websockets_endpoint = 'wss://api.poloniex.com/'

	def __str__(self):
		'''
		Two API clients are the same if they use the same credentials. They must behave equally in respect to all the calls.
		:return: None
		'''
		return json.dumps([self.api_key, self.secret])

	def __eq__(self, other):
		return str(self) == str(other)

	def __ne__(self, other):
		return str(self) != str(other)

	def __get_credentials(self, config_file_path):
		'''
		This method will try to interpret the file on the path in one of three ways:
		* first it will try to interpret it as an ini file (regardless of the file extension)
		* then it will try to interpret it as a JSON file (regardless of the file extension)
		* lastly it will try to interpret it as a Python file (file extension must be py)
		:param config_file_path: absolute path to the config file
		:return: api key, secret and customer id (tuple)
		'''
		api_key = None
		secret = None

		# All of the following tries catch all exceptions that can occur (as there are plenty): missing file,
		# wrong type, misconfigured.
		try:
			config_parser = ConfigParser()
			config_parser.read(config_file_path)
			api_key = config_parser.get('CONFIG', 'apiKey')
			secret = config_parser.get('CONFIG', 'secret')
			return api_key, secret
		except:
			pass

		try:
			with open(config_file_path, 'rb') as file:
				blob = json.loads(file.read().decode())
				api_key = blob.get('apiKey')
				secret = blob.get('secret')
			return api_key, secret
		except:
			pass

		# This is deprecated in python 3.4 (but it will work), so if working with later, try using ini or json approaches instead
		try:
			import importlib.machinery

			loader = importlib.machinery.SourceFileLoader('poloniex.config', config_file_path)
			config = loader.load_module()

			api_key = config.api_key
			secret = config.secret
			return api_key, secret
		except:
			pass

		if api_key is None or secret is None:
			raise Exception(
				'While the config file was found, it was not configured correctly. Check for examples here: {}'.format(
					EXAMPLES_URL))

		return api_key, secret

	def __prepare_request_data(self, params):
		'''
		Returns the signature for the next REST API call. nonce will be a timestamp (time.time()) multiplied by 1000,
		so we include some of the decimal part to reduce the chance of sending the same one more than once.
		:param params - python dict that includes all the parameters for the call
		:return: encoded params, header with signature
		'''
		params['nonce'] = int(time.time() * 1000)
		encoded_params = urllib.parse.urlencode(params).encode('utf8')
		headers = {
			'Sign': hmac.new(self.secret, encoded_params, hashlib.sha512).hexdigest(),
			'Key': self.api_key
		}
		return params, headers

	def ticker(self):
		'''
		This method will call ticker resource and return the result.
		:return: ticker blob (dict)
		'''
		resource = 'public'
		params = {
			'command': 'returnTicker',
		}

		response = requests.get('{}{}'.format(self.api_endpoint, resource), params=params)

		return json.loads(response.text)

	def daily_volume(self):
		'''
		This method will call return last 24 hour volume for all the currency pairs.
		:return: volume blob (dict)
		'''
		resource = 'public'
		params = {
			'command': 'return24hVolume',
		}

		response = requests.get('{}{}'.format(self.api_endpoint, resource), params=params)

		return json.loads(response.text)

	def currencies(self):
		'''
		This method will call return information about all the tradable currencies
		:return: volume blob (dict)
		'''
		resource = 'public'
		params = {
			'command': 'returnCurrencies',
		}

		response = requests.get('{}{}'.format(self.api_endpoint, resource), params=params)

		return json.loads(response.text)

	def order_book(self, pair=None, depth=10):
		'''
		This method will call return last 24 hour volume for all the currency pairs.
		:pair - currency pair for the order book
		:depoth - depth of the order book
		:return: volume blob (dict)
		'''
		resource = 'public'
		params = {
			'command': 'returnOrderBook',
			'depth': depth
		}

		if pair is not None:
			params['currencyPair'] = pair

		response = requests.get('{}{}'.format(self.api_endpoint, resource), params=params)

		return json.loads(response.text)

	def trade_history(self, pair, start, end):
		'''
		This method will call return last 24 hour volume for all the currency pairs.
		:pair - currency pair for the trade history
		:start - Unix timestamp of the start of the interval
		:end - Unix timestamp of the end of the interval
		:return: volume blob (dict)
		'''
		resource = 'public'
		params = {
			'command': 'returnOrderBook',
			'pair': pair,
			'start': start,
			'end': end,
		}

		response = requests.get('{}{}'.format(self.api_endpoint, resource), params=params)

		return json.loads(response.text)

	def chart_data(self, pair, start, end, period=CANDLE_PERIOD_14400):
		'''
		This method will call return last 24 hour volume for all the currency pairs.
		:pair - currency pair for the trade history
		:start - Unix timestamp of the start of the interval
		:end - Unix timestamp of the end of the interval
		:period - period for the candle representation
		:return: volume blob (dict)
		'''
		resource = 'public'
		params = {
			'command': 'returnOrderBook',
			'pair': pair,
			'start': start,
			'end': end,
			'period': period,
		}

		response = requests.get('{}{}'.format(self.api_endpoint, resource), params=params)

		return json.loads(response.text)

	def loan_orders(self, currency):
		'''
		This method will call return last 24 hour volume for all the currency pairs.
		:currency - currency for which to return loan orders
		:return: volume blob (dict)
		'''
		resource = 'public'
		params = {
			'command': 'returnLoanOrders',
			'currency': currency,
		}

		response = requests.get('{}{}'.format(self.api_endpoint, resource), params=params)

		return json.loads(response.text)

	def balances(self):
		'''
		Returns a blob of all the balances the account holds
		:return: balances blob (dict)
		'''
		resource = 'tradingApi'
		params = {
			'command': 'returnBalances',
		}

		params, headers = self.__prepare_request_data(params)
		response = requests.post('{}{}'.format(self.private_api_endpoint, resource), data=params, headers=headers)

		return json.loads(response.text)

	def complete_balances(self):
		'''
		Returns a blob of all the balances the account holds, detailed
		:return: detailed balances blob (dict)
		'''
		resource = 'tradingApi'
		params = {
			'command': 'returnCompleteBalances',
		}

		params, headers = self.__prepare_request_data(params)
		response = requests.post('{}{}'.format(self.private_api_endpoint, resource), data=params, headers=headers)

		return json.loads(response.text)

	def deposit_addresses(self):
		'''
		Returns a blob of all the deposit addresses for all the currencies
		:return: addresses blob (dict)
		'''
		resource = 'tradingApi'
		params = {
			'command': 'returnDepositAddresses',
		}

		params, headers = self.__prepare_request_data(params)
		response = requests.post('{}{}'.format(self.private_api_endpoint, resource), data=params, headers=headers)

		return json.loads(response.text)

	def new_deposit_address(self, currency):
		'''
		Generates a new address for a specified currency
		:param currency: one of the supported currencies
		:return: blob that contains the new address under the key 'response'
		'''
		resource = 'tradingApi'
		params = {
			'command': 'generateNewAddress',
			'currency': currency,
		}

		params, headers = self.__prepare_request_data(params)
		response = requests.post('{}{}'.format(self.private_api_endpoint, resource), data=params, headers=headers)

		return json.loads(response.text)

	def deposits_and_withdrawals(self, start, end):
		'''
		Returns a blob containing all deposits and withdrawals for all currencies
		:param start - Unix timestamp for start of the time interval
		:param end - Unix timestamp for end of the time interval
		:return: blob that contains all deposits and withdrawals
		'''
		resource = 'tradingApi'
		params = {
			'command': 'returnDepositsWithdrawals',
			'start': start,
			'end': end,
		}

		params, headers = self.__prepare_request_data(params)
		response = requests.post('{}{}'.format(self.private_api_endpoint, resource), data=params, headers=headers)

		return json.loads(response.text)

	def open_orders(self, pair='all'):
		'''
		Returns a blob containing all deposits and withdrawals for all currencies
		:param pair - currency pair for which orders are to be fetched
		:return: blob that contains all the open orders for requested currency pairs
		'''
		resource = 'tradingApi'
		params = {
			'command': 'returnOpenOrders',
			'currencyPair': pair,
		}

		params, headers = self.__prepare_request_data(params)
		response = requests.post('{}{}'.format(self.private_api_endpoint, resource), data=params, headers=headers)

		return json.loads(response.text)

	def user_trade_history(self, start, end, pair='all'):
		'''
		Returns a blob containing all trades for the selected currency pair (default timespan is day)
		:param start - Unix timestamp for start of the time interval
		:param end - Unix timestamp for end of the time interval
		:param pair - currency pair for which orders are to be fetched
		:return: blob that contains all the trades for the specified currency pair and timespan
		'''
		resource = 'tradingApi'
		params = {
			'command': 'returnTradeHistory',
			'currencyPair': pair,
			'start': start,
			'end': end,
		}

		params, headers = self.__prepare_request_data(params)
		response = requests.post('{}{}'.format(self.private_api_endpoint, resource), data=params, headers=headers)

		return json.loads(response.text)

	def order_trades(self, order_id):
		'''
		Returns a blob containing all trades for the specified order. If no trades are present for the order or if order
		doesn't belong to the user calling, expect an error
		:param order_id - Order id
		:return: blob that contains all the trades for the specified order
		'''
		resource = 'tradingApi'
		params = {
			'command': 'returnOrderTrades',
			'orderNumber': order_id,
		}

		params, headers = self.__prepare_request_data(params)
		response = requests.post('{}{}'.format(self.private_api_endpoint, resource), data=params, headers=headers)

		return json.loads(response.text)

	def cancel_order(self, order_id):
		'''
		Cancel an order
		:param order_id - Order id
		:return: blob that contains success or failure data
		'''
		resource = 'tradingApi'
		params = {
			'command': 'cancelOrder',
			'orderNumber': order_id,
		}

		params, headers = self.__prepare_request_data(params)
		response = requests.post('{}{}'.format(self.private_api_endpoint, resource), data=params, headers=headers)

		return json.loads(response.text)

	def buy(self, currency_pair, rate, amount, post_only=1, fill_or_kill=0, immediate_or_cancel=0):
		'''
		Places a buy order
		:param currency_pair - Selected currency pair
		:param rate - rate or price for this order
		:param amount - amount of the counter that you wish to buy
		:return: blob that contains the placed order data
		'''
		resource = 'tradingApi'
		params = {
			'command': 'buy',
			'currencyPair': currency_pair,
			'rate': rate,
			'amount': amount,
			'fillOrKill': fill_or_kill,
			'immediateOrCancel': immediate_or_cancel,
			'postOnly': post_only,
		}

		params, headers = self.__prepare_request_data(params)
		response = requests.post('{}{}'.format(self.private_api_endpoint, resource), data=params, headers=headers)

		return json.loads(response.text)

	def sell(self, currency_pair, rate, amount, post_only=1, fill_or_kill=0, immediate_or_cancel=0):
		'''
		Places a sell order
		:param currency_pair - Selected currency pair
		:param rate - rate or price for this order
		:param amount - amount of the counter that you wish to sell
		:return: blob that contains the placed order data
		'''
		resource = 'tradingApi'
		params = {
			'command': 'sell',
			'currencyPair': currency_pair,
			'rate': rate,
			'amount': amount,
			'fillOrKill': fill_or_kill,
			'immediateOrCancel': immediate_or_cancel,
			'postOnly': post_only,
		}

		params, headers = self.__prepare_request_data(params)
		response = requests.post('{}{}'.format(self.private_api_endpoint, resource), data=params, headers=headers)

		return json.loads(response.text)

	def fee_info(self):
		'''
		Fetches fee data
		:return: blob that contains the fee data
		'''
		resource = 'tradingApi'
		params = {
			'command': 'returnFeeInfo',
		}

		params, headers = self.__prepare_request_data(params)
		response = requests.post('{}{}'.format(self.private_api_endpoint, resource), data=params, headers=headers)

		return json.loads(response.text)

	def available_balances(self, account='exchange'):
		'''
		Fetches available balance data
		:return: blob that contains the available balances
		'''
		resource = 'tradingApi'
		params = {
			'command': 'returnAvailableAccountBalances',
			'account': account,
		}

		params, headers = self.__prepare_request_data(params)
		response = requests.post('{}{}'.format(self.private_api_endpoint, resource), data=params, headers=headers)

		return json.loads(response.text)

	def attach_trollbox(self, callback):
		'''
		Attach your method to a websocket trollbox channel
		:param callback: this method should accept the following parameters: type, message number, username, message, reputation
		:return:
		'''
		def trollbox_wrapper(wrapped_callback):
			def wrapper(*args, **kwargs):
				message_type = args[0]
				message_number = args[1]
				username = args[2]
				message = args[3]
				reputation = args[4]

				wrapped_callback(message_type, message_number, username, message, reputation)

			return wrapper

		class Trollbox(ApplicationSession):
			def onJoin(self, details):
				yield self.subscribe(trollbox_wrapper(callback), 'trollbox')

		if self.runner is None:
			self.runner = ApplicationRunner(url=self.websockets_endpoint, realm='realm1')
		self.runner.run(Trollbox)

	def attach_ticker(self, callback):
		'''
		Attach your method to a websocket channel
		:param callback: this method should accept the following parameters: currency pair, last, lowest ask, highest bid, percent change, base volume, quote volume, is frozen, 24hr high, 24hr low
		:return:
		'''

		def ticker_wrapper(wrapped_callback):
			def wrapper(*args, **kwargs):
				currency_pair = args[0]
				last = decimal.Decimal(args[1])
				lowest_ask = decimal.Decimal(args[2])
				highest_bid = decimal.Decimal(args[3])
				change = decimal.Decimal(args[4])
				base_volume = decimal.Decimal(args[5])
				quote_volume = decimal.Decimal(args[6])
				is_frozen = args[7] == 1
				high = decimal.Decimal(args[8])
				low = decimal.Decimal(args[9])

				wrapped_callback(currency_pair, last, lowest_ask, highest_bid, change, base_volume, quote_volume, is_frozen, high, low)

			return wrapper

		class Ticker(ApplicationSession):
			def onJoin(self, details):
				yield self.subscribe(ticker_wrapper(callback), 'ticker')

		if self.runner is None:
			self.runner = ApplicationRunner(url=self.websockets_endpoint, realm='realm1')
		self.runner.run(Ticker)

	def attach_order_book(self, callback, currency_pair):
		'''
		Attach a method to a websocket channel for orderbook of your choice
		:param callback: this method should accept the following parameters: modifications, removals, trades, sequence
		:param currency_pair: the pair for which one wishes to follow the order book
		:return:
		'''
		def order_book_wrapper(wrapped_callback):
			def wrapper(*args, **kwargs):
				modifications = []
				removals = []
				trades = []
				for arg in args:
					blob = {}
					data = arg.get('data')

					if arg.get('type') == 'orderBookModify':
						blob = {
							'amount': decimal.Decimal(data.get('amount')),
							'rate': decimal.Decimal(data.get('rate')),
							'type': data.get('type'),
						}
						modifications.append(blob)
					elif arg.get('type') == 'orderBookRemove':
						blob = {
							'rate': decimal.Decimal(data.get('rate')),
							'type': data.get('type'),
						}
						removals.append(blob)
					else:  # New trade
						blob = {
							'tradeID': data.get('tradeID'),
							'rate': decimal.Decimal(data.get('rate')),
							'amount': decimal.Decimal(data.get('amount')),
							'total': decimal.Decimal(data.get('total')),
							'date': datetime.datetime.strptime(data.get('date'), '%Y-%m-%d %H:%M:%S'),
							'type': data.get('type'),
						}
						from pprint import pprint
						pprint(blob)
						trades.append(blob)

				wrapped_callback(modifications, removals, trades, **kwargs)

			return wrapper

		class OrderBook(ApplicationSession):
			def onJoin(self, details):
				yield self.subscribe(order_book_wrapper(callback), currency_pair)

		if self.runner is None:
			self.runner = ApplicationRunner(url=self.websockets_endpoint, realm='realm1')
		self.runner.run(OrderBook)
