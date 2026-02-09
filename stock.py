import os
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest

# =====================
# CONFIG
# =====================
STOCKS = ["NVDA", "MSFT", "GOOGL", "AAPL"]
MAX_SHARES = 200          # Maximum per stock
BUY_AMOUNT = 200           # How many shares you want to hold per stock
STOP_LOSS_PCT = 0.07      # 7% stop loss
TAKE_PROFIT_PCT = 0.10    # 10% take profit
PAPER = True              # Paper trading

# =====================
# LOAD SECRETS
# =====================
API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_SECRET_KEY")

print("DEBUG:")
print("API key exists:", API_KEY is not None)
print("Secret key exists:", API_SECRET is not None)

if not API_KEY or not API_SECRET:
    raise ValueError("ALPACA_API_KEY or ALPACA_SECRET_KEY not set!")

# =====================
# CLIENTS
# =====================
trading_client = TradingClient(API_KEY, API_SECRET, paper=PAPER)
data_client = StockHistoricalDataClient(API_KEY, API_SECRET)
print("Alpaca clients initialized")

# =====================
# FETCH CURRENT PRICES
# =====================
current_prices = {}
for symbol in STOCKS:
    trade_req = StockLatestTradeRequest(symbol_or_symbols=symbol)
    latest_trade = data_client.get_stock_latest_trade(trade_req)[symbol]
    current_prices[symbol] = float(latest_trade.price)
    print(f"{symbol} current price: {current_prices[symbol]}")

# =====================
# GET ALL POSITIONS
# =====================
positions = trading_client.get_all_positions()
positions_dict = {p.symbol: p for p in positions}

# =====================
# LOOP OVER EACH STOCK
# =====================
for symbol in STOCKS:
    current_price = current_prices[symbol]
    position = positions_dict.get(symbol)

    if position:  # Already own shares
        qty = int(position.qty)
        avg_entry = float(position.avg_entry_price)
        stop_price = avg_entry * (1 - STOP_LOSS_PCT)
        take_profit_price = avg_entry * (1 + TAKE_PROFIT_PCT)

        print(f"\nPosition: {symbol}, Qty: {qty}, Avg entry: {avg_entry}")
        print(f"Stop loss at: {stop_price}, Take profit at: {take_profit_price}")

        if current_price <= stop_price:
            print(f"STOP LOSS HIT for {symbol} — SELLING")
            order = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )
            trading_client.submit_order(order)
            print("Sell order submitted")

        elif current_price >= take_profit_price:
            print(f"TAKE PROFIT HIT for {symbol} — SELLING")
            order = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )
            trading_client.submit_order(order)
            print("Sell order submitted")

        else:
            print(f"HOLD {symbol} — current price: {current_price}, shares held: {qty}")

    else:  # No position yet → buy up to BUY_AMOUNT
        qty_to_buy = min(BUY_AMOUNT, MAX_SHARES)
        print(f"\nNo position for {symbol}. Buying {qty_to_buy} shares")
        order = MarketOrderRequest(
            symbol=symbol,
            qty=qty_to_buy,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY
        )
        trading_client.submit_order(order)
        print(f"Buy order submitted for {symbol}")

print("\nStock Bot run complete.")
