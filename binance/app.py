from binance.client import Client
from binance.agent import Agent
from binance.tokenpair import TokenPair
import pickle

API_KEY = '6qU8SOwMNuSCnQsUddXcFPt6e3jkQPOhhsM77H4Y2gQc6oXFjrDdXmIdsdXrkfXZ'
API_SECRET = '6S31vqIj54vQ9FQKKue6FMulMSxGZh5DxizjZOlXuDvq7LIKHYzAFkVTNhoX2j3Y'

client = Client(API_KEY, API_SECRET)
# info = client.get_account()
# print "info: ", info
# balance = client.get_asset_balance(asset='BTC')
# print "balance: ", balance
# status = client.get_account_status()
# print "status: ", status
# tickers = client.get_ticker(symbol="BNBBTC")
# print(tickers)

# create token pair to monitor and trading
BNNBTC_pair = TokenPair(client, "BNBBTC")
VENETH_pair = TokenPair(client, "VENETH")
ONTETH_pair = TokenPair(client, "ONTETH")

agent = Agent(client)
# our token must add these tokens in order to perform action like: monitoringm trading...
agent.add_token_pair(BNNBTC_pair)
agent.add_token_pair(VENETH_pair)
agent.add_token_pair(ONTETH_pair)
# run the agent
agent.run()

