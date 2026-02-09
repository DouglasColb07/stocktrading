import os
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest

# =====================
# CONFIG
# =====================
SYMBOL = "AAPL"        # <-- change this for the next stock
MAX_SHARES = 80
BUY_AMOUNT = 80        # how many shares you WANT total
STOP_LOSS_PCT = 0.07   # 7% stop loss
TAKE_PROFIT_PCT = 0.10 # 10% take profit
PAPER = True

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
# GET CURRENT PRICE
# =====================
trade_req = StockLatestTradeRequest(symbol_or_symbols=SYMBOL)
latest_trade = data_client.get_stock_latest_trade(trade_req)[SYMBOL]
current_price = float(latest_trade.price)

print(f"{SYMBOL} current price: {current_price}")

# =====================
# CHECK EXISTING POSITION
# =====================
positions = trading_client.get_all_positions()
position = next((p for p in positions if p.symbol == SYMBOL), None)

# =====================
# IF WE OWN THE STOCK → CHECK SELL RULES
# =====================
if position:
    qty = int(position.qty)
    avg_entry = float(position.avg_entry_price)

    stop_price = avg_entry * (1 - STOP_LOSS_PCT)
    take_profit_price = avg_entry * (1 + TAKE_PROFIT_PCT)

    print(f"Position found: {qty} shares @ {avg_entry}")
    print(f"Stop loss at: {stop_price}")
    print(f"Take profit at: {take_profit_price}")

    if current_price <= stop_price:
        print("STOP LOSS HIT — SELLING")
        order = MarketOrderRequest(
            symbol=SYMBOL,
            qty=qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY
        )
        trading_client.submit_order(order)
        print("Sell order submitted")

    elif current_price >= take_profit_price:
        print("TAKE PROFIT HIT — SELLING")
        order = MarketOrderRequest(
            symbol=SYMBOL,
            qty=qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY
        )
        trading_client.submit_order(order)
        print("Sell order submitted")

    else:
        print("Holding position — no sell condition met")

# =====================
# IF WE DON'T OWN ENOUGH → BUY
# =====================
else:
    qty_to_buy = min(BUY_AMOUNT, MAX_SHARES)

    print(f"No position found. Buying {qty_to_buy} shares")

    order = MarketOrderRequest(
        symbol=SYMBOL,
        qty=qty_to_buy,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY
    )
    trading_client.submit_order(order)
    print("Buy order submitted")

print("Bot run complete")
