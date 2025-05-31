from alpaca.data import StockDataStream
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest

class MarketData:
    stock_stream = StockDataStream("api-key", "secret-key")
    historical_client = StockHistoricalDataClient('api-key', 'secret-key')

    def get_quote(self, ticker):
        request_params = StockLatestQuoteRequest(symbol_or_symbols=[ticker])

        latest_quotes = self.historical_client.get_stock_latest_quote(request_params)

        gld_latest_ask_price = latest_multisymbol_quotes["GLD"].ask_price

