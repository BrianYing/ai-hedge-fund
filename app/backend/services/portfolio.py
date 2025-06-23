from app.backend.trade.alpaca_client.order import Alpaca


def create_portfolio(initial_cash: float, margin_requirement: float, tickers: list[str]) -> dict:
  return {
        "cash": initial_cash,  # Initial cash amount
        "margin_requirement": margin_requirement,  # Initial margin requirement
        "margin_used": 0.0,  # total margin usage across all short positions
        "positions": {
            ticker: {
                "long": 0,  # Number of shares held long
                "short": 0,  # Number of shares held short
                "long_cost_basis": 0.0,  # Average cost basis for long positions
                "short_cost_basis": 0.0,  # Average price at which shares were sold short
                "short_margin_used": 0.0,  # Dollars of margin used for this ticker's short
            }
            for ticker in tickers
        },
        "realized_gains": {
            ticker: {
                "long": 0.0,  # Realized gains from long positions
                "short": 0.0,  # Realized gains from short positions
            }
            for ticker in tickers
        },
    }

def create_alpaca_portfolio(margin_requirement: float, tickers: list[str]) -> dict:
    alpaca_client = Alpaca()

    positions = {}
    realized_gains = {}
    for ticker in tickers:
       pos = alpaca_client.get_single_position(ticker)
       positions[ticker] = {
          "long": int(pos.qty) if pos else 0,  # Number of shares held long
          "short": 0,  # No short positions tracked here
          "long_cost_basis": float(pos.avg_entry_price) if pos else 0.0,  # Average cost basis for long positions
          "short_cost_basis": 0.0,  # No short positions tracked here
          "short_margin_used": 0.0,  # No short positions tracked here
       }
       realized_gains[ticker] = {
            "long": 0.0,  # Realized gains from long positions
            "short": 0.0,  # Realized gains from short positions
       }

    return {
        "cash": float(alpaca_client.account.cash),
        "margin_requirement": margin_requirement,
        "margin_used": 0.0,
        "positions": positions,
        "realized_gains": realized_gains,
    }
