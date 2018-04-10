from binance.enums import Action, MarketState
import pickle

class TokenPair:

    def __init__(self, client, name):
        self.market_state = MarketState.STABLE
        # we'll use this client instance to get market data, make order...
        self.client = client
        # name of token pair, for example: BNBBTC
        self.name = name
        # the most recent price and quantity when we bought this token
        self.last_buy_price = 0.0
        self.last_buy_quantity = 0
        # the most recent price and quantity when we sold this token
        self.last_sell_price = 0.0
        self.last_sell_quantity = 0
        # action that we've made recently
        self.last_action = Action.WAIT
        self.last_active_action = Action.WAIT
        # current token's price
        tickers = client.get_ticker(symbol='VENETH')
        self.price = float(tickers['lastPrice'])
        # our budget, if token's name is BNBBTC, then the first element of this array is our BNB balance and
        # the second one is BTC balance
        self.balance = [100, 1.0]
        self.profit = 0.0
        # prices_dict = pickle.load(open("price_history.txt", 'r+'))
        # prices = prices_dict[self.name]
        # self.last_buy_price = prices['last_buy_price']
        # self.last_sell_price = prices['last_sell_price']
        # # init the prices based on last price we've seen in market
        # if self.last_buy_price == 0 and self.last_sell_price == 0:
        #     tickers = client.get_ticker(symbol=self.name)
        #     self.last_buy_price = float(tickers['lastPrice'])
        #     self.last_sell_price = float(tickers['lastPrice'])

    # helper method to get total amount of coin have been traded
    def get_average_price(self, agg_trades):
        total_quantity = 0.0
        total_coin_traded = 0.0
        for trade in agg_trades:
            total_quantity += float(trade['q'])
            total_coin_traded += float(trade['q']) * float(trade['p'])
        # prevent divide by zero
        if total_quantity > 0:
            return total_coin_traded / total_quantity
        else:
            return self.price

    # def summary_trade_recently(self, start_str):
    #     agg_trades = self.client.aggregate_trade_iter(symbol=self.name, start_str=start_str)
    #     # iterate over the trade iterator and get the average values of trade history
    #     average_price = self.get_average_price(agg_trades)
    #     print("average price: %.8f" % average_price)
    #     self.price_change += average_price - self.price
    #     if self.price_change > 0.0:
    #         print("price increasing: %.8f" % self.price_change)
    #         self.market_state = MarketState.INCREASE_NORMAL
    #     elif self.price_change < 0.0:
    #         print("price decreasing: %.8f" % self.price_change)
    #         self.market_state = MarketState.DECREASE_NORMAL
    #     else:
    #         self.market_state = MarketState.STABLE
    #
    #     # update to the most recent average price
    #     self.price = average_price
    #     return self.market_state, average_price

    def get_pending_orders(self):
        return self.client.get_open_orders(symbol=self.name)

    def buy(self, params):

        if self.balance[1] < params:
            print "%s cant buy anymore, short of money!!!" % self.name
            self.last_action = "wait"
        else:
            buy_amount = int(self.balance[1] / params)
            self.balance[0]  += buy_amount
            self.balance[1] -= buy_amount * params
            self.last_buy_price = params
            self.last_action = "buy"
            self.last_buy_quantity = buy_amount
            print "buy %s, price: %.8f, amount: %d" % (self.name, params, buy_amount)


    def sell(self, params):
        if self.balance[0] > 0:
            sell_amount = self.balance[0]
            self.balance[1] += sell_amount * params
            self.balance[0] = 0
            self.last_sell_price = params
            self.last_action = "sell"
            self.last_sell_quantity = sell_amount
            print "sell %s, price: %.8f, amount: %d" % (self.name, params, sell_amount)
        else:
            print "%s cant sell anymore, short of token!!!" % self.name
            self.last_action = "wait"


    def cancel_order(self, params):
        print("cancel order")

