from binance.enums import MarketState, Action, Actions, States
import time
import pandas as pd
import numpy as np
import sys, traceback
import pickle

from binance.helpers import date_to_milliseconds

EPSILON = 0.9
ALPHA = 0.1     # learning rate
GAMMA = 0.9    # discount factor

class Agent:

    def __init__(self, client):
        self.token_pairs = []
        self.client = client
        # self.table = self.build_q_table(states=States, actions=Actions)

    # def choose_action(self, state):
    #     state_action = self.table.loc[state, :]
    #     if np.random.uniform() > EPSILON or (state_action == 0).all():
    #         action = np.random.choice(Actions)
    #     else:
    #         action = state_action.idxmax()
    #     return action
    #
    # @staticmethod
    # def get_env_feedback(token_pair, action, start_str):
    #     # TODO calculate reward based on actions
    #     market_state, last_price = token_pair.summary_trade_recently(start_str)
    #     reward = 0
    #     if action == "buy":
    #         if token_pair.last_active_action == Action.BUY:
    #             reward += (token_pair.last_buy_price - last_price) * token_pair.last_buy_quantity / 2
    #         else:
    #             reward += (token_pair.last_sell_price - last_price) * token_pair.last_sell_quantity
    #     elif action == "sell":
    #         if token_pair.last_active_action == Action.BUY:
    #             reward += (last_price - token_pair.last_buy_price) * token_pair.last_buy_quantity
    #         else:
    #             reward += (last_price - token_pair.last_sell_price) * token_pair.last_sell_quantity / 2
    #
    #     elif action == "wait":
    #         if token_pair.last_active_action == Action.BUY:
    #             reward += (last_price - token_pair.last_buy_price) * token_pair.last_buy_quantity
    #         else:
    #             reward += (token_pair.last_sell_price - last_price) * token_pair.last_sell_quantity
    #
    #     else:
    #         pass
    #
    #     token_pair.last_action = action
    #     if action == Action.BUY or action == Action.SELL:
    #         token_pair.last_active_action = action
    #
    #     return market_state, reward
    #
    # @staticmethod
    # def build_q_table(states, actions):
    #     return pd.DataFrame(index=states, columns=actions, data=np.zeros((len(states), len(actions))))

    def add_token_pair(self, new_pair):
        self.token_pairs.append(new_pair)

    def remove_token_pair(self, token_pair_name):
        self.token_pairs.remove(token_pair_name)

    @staticmethod
    def get_selling_summary(sell_orders):
        price = 0.0
        sell_quantity = 0
        for sell_order in sell_orders:
            sell_quantity += float(sell_order[1])
            price += float(sell_order[1]) * float(sell_order[0])
        sell_average_price = price / sell_quantity
        return sell_average_price, sell_quantity

    @staticmethod
    # this function we add some code to get exact bid price,
    # because the bid price can be fake if user has a lot of money
    def get_buying_summary(buy_orders, sell_quantity):
        buy_quantity = 0
        real_price = 0.0
        real_buy_quantity = 0
        for buy_order in buy_orders:
            buy_order[0] = float(buy_order[0])
            buy_order[1] = float(buy_order[1])
            if real_buy_quantity + buy_order[1] < sell_quantity:
                real_buy_quantity += buy_order[1]
                real_price += buy_order[1] * buy_order[0]
            buy_quantity += buy_order[1]
        real_avg_buy_price = real_price / real_buy_quantity
        return real_avg_buy_price, buy_quantity

    @staticmethod
    def check_profit(token_pair, buy_orders, sell_orders):
        # check profit based on the last orders we've made and the newest orders that match our orders
        if token_pair.last_action == "buy":
            # search for sell orders that sell token with price lower than or equal our bid price
            for order in sell_orders:
                ask_price = float(order[0])
                if ask_price <= token_pair.last_buy_price:
                    token_pair.profit += (token_pair.last_sell_price - ask_price) * token_pair.last_sell_quantity
                    token_pair.last_action = "wait"
                    print("%s profit: %f" % (token_pair.name, token_pair.profit))
                    break

        if token_pair.last_action == "sell":
            # search for buy orders that buy token with price higher than or equal our bid price
            for order in buy_orders:
                bid_price = float(order[0])
                if bid_price >= token_pair.last_sell_price:
                    token_pair.profit += (bid_price - token_pair.last_buy_price) * token_pair.last_buy_quantity
                    token_pair.last_action = "wait"
                    print("%s profit: %f" % (token_pair.name, token_pair.profit))
                    break

    def get_average_price(self, order_book, token_pair):
        # buy orders
        buy_orders = order_book['bids']
        # sell orders
        sell_orders = order_book['asks']
        sell_average_price, sell_quantity = self.get_selling_summary(sell_orders)
        buy_average_price, buy_quantity = self.get_buying_summary(buy_orders, sell_quantity)
        sell_average_price = float(sell_average_price)
        buy_average_price = float(buy_average_price)
        # check and print out profit that we've made so far
        self.check_profit(token_pair, buy_orders, sell_orders)

        market_status = "stable"
        if buy_quantity > sell_quantity * 1.3:
            market_status = "increase"

        if sell_quantity > buy_quantity * 1.3:
            market_status = "decrease"

        if market_status == "increase":
            buy_order = buy_orders[len(buy_orders) / 4]
            if float(buy_order[0]) * 1.05 < token_pair.last_sell_price and token_pair.last_action != "buy":
                token_pair.buy(float(buy_order[0]))

        if market_status == "decrease":
            sell_order = sell_orders[len(sell_orders) / 4]
            if float(sell_order[0]) > token_pair.last_buy_price * 1.05 and token_pair.last_action != "sell":
                token_pair.sell(float(sell_order[0]))

        print ("%s market state: %s" % (token_pair.name, market_status))

        # delete pending orders that live too long
        pending_orders = token_pair.get_pending_orders()
        for pending_order in pending_orders:
            if pending_order['time'] < date_to_milliseconds("10 minute ago UTC"):
                token_pair.cancel_order(pending_order['orderId'])

        return buy_average_price, sell_average_price, buy_quantity, sell_quantity

    def trade(self):
        for token_pair in self.token_pairs:
            # get market depth
            order_book = self.client.get_order_book(symbol=token_pair.name, limit=50)
            buy_avg, sell_avg, buy_qnt, sell_qnt = self.get_average_price(order_book, token_pair)
            print ("%s: buy avg price: %.8f, buy quantity: %d, sell avg price: %.8f, sell amount: %d" %
                   (token_pair.name, buy_avg, buy_qnt, sell_avg, sell_qnt))

    def run(self):
        # get price history from file
        price_dict = pickle.load(open('price_history.txt', 'r+'))
        for token_pair in self.token_pairs:
            if token_pair.name not in price_dict:
                tickers = self.client.get_ticker(symbol=token_pair.name)
                history_dict = {}
                history_dict['last_buy_price'] = float(tickers['lastPrice'])
                history_dict['last_sell_price'] = float(tickers['lastPrice'])
                price_dict[token_pair.name] = history_dict

            price_history = price_dict[token_pair.name]
            # this is used for demo only, we set the bid and ask price
            # a little bit lower or higher so our bot can start buying or selling quickly
            token_pair.last_buy_price = price_history['last_buy_price'] * 0.9
            token_pair.last_sell_price = price_history['last_sell_price'] * 1.1
        # start trading
        try:
            while True:
                time.sleep(15)
                self.trade()
        except Exception as e:
            print e
            traceback.print_exc(file=sys.stdout)


    # two functions below are for reinforcement learning, do not touch
    def learn(self, period=15):
        print("Agent is running...")
        start_str = '%d second ago UTC' % period
        for token_pair in self.token_pairs:
            token_pair.summary_trade_recently(start_str)
        loop = 1
        while True:
            for token_pair in self.token_pairs:
                current_state = token_pair.market_state
                action = self.choose_action(current_state)
                self.perform_action(action, token_pair)
                time.sleep(period)
                next_state, reward = self.get_env_feedback(token_pair, action, start_str)
                q_predict = self.table.loc[current_state, action]
                q_target = reward + GAMMA * self.table.loc[next_state, :].max()
                self.table.loc[current_state, action] += ALPHA * (q_target - q_predict)

            loop += 1
            if loop == 5:
                print(self.table)
                loop = 1

    def perform_action(self, action, token_pair):
        if action == "buy":
            token_pair.buy(None)
        elif action == "sell":
            token_pair.sell(None)
        elif action == "cancel_order":
            token_pair.cancel_order(None)
        else:
            pass
