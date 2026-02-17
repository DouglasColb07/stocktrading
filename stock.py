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
TAKE_PROFIT_PCT = 0.10
SHORT_MA = 5
LONG_MA = 20
PAPER = True

# =====================
# LOAD SECRETS
# =====================
API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_SECRET_KEY")

if not API_KEY or not API_SECRET:
    raise ValueError("ALPACA_API_KEY or ALPACA_SECRET_KEY not set!")

# =====================
# CLIENTS
# =====================
trading_client = TradingClient(API_KEY, API_SECRET, paper=PAPER)
data_client = StockHistoricalDataClient(API_KEY, API_SECRET)

# =====================
# HELPER FUNCTIONS
# =====================
def get_moving_average(symbol, short=True):
    bars_req = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Minute,
        limit=LONG_MA
    )
    bars = data_client.get_stock_bars(bars_req)[symbol]
    prices = [bar.c for bar in bars]
    return sum(prices[-SHORT_MA:]) / SHORT_MA if short else sum(prices[-LONG_MA:]) / LONG_MA

def buy_stock(symbol, qty):
    order = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY
    )
    trading_client.submit_order(order)
    print(f"BUY: {qty} shares of {symbol}")

def sell_stock(symbol, qty):
    order = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.SELL,
        time_in_force=TimeInForce.DAY
    )
    trading_client.submit_order(order)
    print(f"SELL: {qty} shares of {symbol}")

# =====================
# MAIN BOT LOGIC
# =====================
positions = trading_client.get_all_positions()
positions_dict = {p.symbol: p for p in positions}

for symbol in STOCKS:
    short_ma = get_moving_average(symbol, short=True)
    long_ma = get_moving_average(symbol, short=False)
    print(f"{symbol} - Short MA: {short_ma}, Long MA: {long_ma}")

    position = positions_dict.get(symbol)
    qty_held = int(position.qty) if position else 0
    avg_price = float(position.avg_entry_price) if position else 0

    # Latest price for stop-loss / take-profit
    bars_req = StockBarsRequest(symbol_or_symbols=symbol, timeframe=TimeFrame.Minute, limit=1)
    latest_price = data_client.get_stock_bars(bars_req)[symbol][-1].c

    # ========= IDEA 5 LOGIC =========
    # Buy if short MA crosses above long MA
    if short_ma > long_ma and qty_held < MAX_SHARES:
        qty_to_buy = min(BUY_AMOUNT, MAX_SHARES - qty_held)
        buy_stock(symbol, qty_to_buy)

    # Sell if short MA crosses below long MA or stop-loss / take-profit triggered
    elif qty_held > 0:
        stop_price = avg_price * (1 - STOP_LOSS_PCT)
        take_profit_price = avg_price * (1 + TAKE_PROFIT_PCT)

        if short_ma < long_ma:
            sell_stock(symbol, qty_held)
        elif latest_price <= stop_price:
            print(f"STOP LOSS triggered for {symbol}")
            sell_stock(symbol, qty_held)
        elif latest_price >= take_profit_price:
            print(f"TAKE PROFIT triggered for {symbol}")
            sell_stock(symbol, qty_held)
        else:
            print(f"HOLD {symbol}: {qty_held} shares, latest price: {latest_price}")

print("Stock Bot run complete.")
