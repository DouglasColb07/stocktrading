import os
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

# =====================
# CONFIG
# =====================
STOCKS = ["NVDA", "GOOGL", "AAPL", "COST"]
MAX_SHARES = 100
BUY_AMOUNT = 100
STOP_LOSS_PCT = 0.07
SHORT_MA = 5
LONG_MA = 20
PAPER = True

# =====================
# LOAD API KEYS FROM GITHUB SECRETS
# =====================
API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_SECRET_KEY")

if not API_KEY or not API_SECRET:
    raise ValueError("ALPACA_API_KEY or ALPACA_SECRET_KEY not set!")

# =====================
# CREATE CLIENTS
# =====================
trading_client = TradingClient(API_KEY, API_SECRET, paper=PAPER)
data_client = StockHistoricalDataClient(API_KEY, API_SECRET)

# =====================
# GET MOVING AVERAGE
# =====================
def get_moving_averages(symbol):
    bars_req = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Minute,
        limit=LONG_MA
    )

    bars = data_client.get_stock_bars(bars_req).data[symbol]

    if len(bars) < LONG_MA:
        return None, None

    prices = [bar.close for bar in bars]  # FIXED (.close instead of .c)

    short_ma = sum(prices[-SHORT_MA:]) / SHORT_MA
    long_ma = sum(prices[-LONG_MA:]) / LONG_MA

    return short_ma, long_ma


# =====================
# BUY FUNCTION
# =====================
def buy_stock(symbol, qty):
    order = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY
    )
    trading_client.submit_order(order)
    print(f"BUY {qty} shares of {symbol}")


# =====================
# SELL FUNCTION
# =====================
def sell_stock(symbol, qty):
    order = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.SELL,
        time_in_force=TimeInForce.DAY
    )
    trading_client.submit_order(order)
    print(f"SELL {qty} shares of {symbol}")


# =====================
# MAIN BOT LOGIC
# =====================
print("Starting 30-min trading bot...")

positions = trading_client.get_all_positions()
positions_dict = {p.symbol: p for p in positions}

for symbol in STOCKS:
    print(f"\nChecking {symbol}")

    short_ma, long_ma = get_moving_averages(symbol)

    if short_ma is None:
        print("Not enough data yet.")
        continue

    print(f"Short MA: {short_ma}")
    print(f"Long MA: {long_ma}")

    position = positions_dict.get(symbol)
    qty_held = int(position.qty) if position else 0
    avg_price = float(position.avg_entry_price) if position else 0

    # Get latest price
    bars_req = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Minute,
        limit=1
    )

    latest_bar = data_client.get_stock_bars(bars_req).data[symbol][0]
    latest_price = latest_bar.close

    # =====================
    # BUY SIGNAL
    # =====================
    if short_ma > long_ma and qty_held < MAX_SHARES:
        qty_to_buy = min(BUY_AMOUNT, MAX_SHARES - qty_held)
        buy_stock(symbol, qty_to_buy)

    # =====================
    # SELL SIGNAL
    # =====================
    elif qty_held > 0:

        stop_price = avg_price * (1 - STOP_LOSS_PCT)

        if short_ma < long_ma:
            print("MA crossover SELL signal")
            sell_stock(symbol, qty_held)

        elif latest_price <= stop_price:
            print("STOP LOSS triggered")
            sell_stock(symbol, qty_held)

        else:
            print(f"HOLD {symbol} | Shares: {qty_held} | Price: {latest_price}")

print("\nBot run complete.")
