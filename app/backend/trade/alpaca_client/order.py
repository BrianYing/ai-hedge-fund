import os

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.models import Position


class Alpaca:
    alpaca_key = os.getenv("ALPACA_API_KEY")
    alpaca_secret = os.getenv("ALPACA_API_SECRET")
    trading_client = TradingClient(alpaca_key, alpaca_secret, paper=True)
    account = trading_client.get_account()

    def get_buying_power(self):
        return self.account.buying_power

    def asset_tradable(self, ticker):
        return self.trading_client.get_asset(ticker).tradable

    def get_single_position(self, ticker) -> Position:
        try:
            position = self.trading_client.get_open_position(ticker)
            print("{} shares of {}".format(position.qty, position.symbol))
            return position
        except Exception as e:
            print("{} shares of {}".format(0, ticker))
            return None 


    def get_all_position(self):
        portfolio = self.trading_client.get_all_positions()
        for position in portfolio:
            print("{} shares of {}".format(position.qty, position.symbol))

    def market_order(self, ticker, qty, is_buy=True):
        market_order_data = MarketOrderRequest(
            symbol=ticker,
            qty=qty,
            side=OrderSide.BUY if is_buy else OrderSide.SELL,
            time_in_force=TimeInForce.DAY
        )

        self.trading_client.submit_order(
            order_data=market_order_data
        )

    def limit_order(self, ticker, limit_price, qty):
        limit_order_data = LimitOrderRequest(
            symbol=ticker,
            limit_price=limit_price,
            notional=4000,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.FOK
        )

        self.trading_client.submit_order(
            order_data=limit_order_data
        )
