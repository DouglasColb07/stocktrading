# =============================
# Imports
# =============================
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockQuotesRequest
from datetime import datetime, time
import time as t  # for sleep

# =============================
# Alpaca API keys (Paper Trading)
# =============================
API_KEY = "PKSIVZHEUMOCR4KHFTUYIWDYMH"
API_SECRET = "2D1eYP4xGmk89XgYGW4ZGnUJoBFeB2w4eZgNNgmprPAG"

trading_client = TradingClient(API_KEY, API_SECRET, paper=True)
data_client = StockHistoricalDataClient(API_KEY, API_SECRET)

# =============================
# BST Node Class
# =============================
class Node:
    def __init__(self, stock_symbol, buy_price, stop_loss, take_profit):
        self.stock_symbol = stock_symbol
        self.buy_price = buy_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.left = None
        self.right = None

# =============================
# BST Insert Function (uses real-time price)
# =============================
def insert_trade(node, stock_symbol, stop_loss_pct, take_profit_pct):
    # Fetch current price
    request = StockQuotesRequest(symbol_or_symbols=[stock_symbol])
    quote = data_client.get_stock_quotes(request)
    buy_price = quote[stock_symbol][-1].ask_price

    # Calculate stop-loss and take-profit based on percentage
    stop_loss = buy_price * (1 - stop_loss_pct)
    take_profit = buy_price * (1 + take_profit_pct)

    if node is None:
        return Node(stock_symbol, buy_price, stop_loss, take_profit)

    if buy_price < node.buy_price:
        node.left = insert_trade(node.left, stock_symbol, stop_loss_pct, take_profit_pct)
    else:
        node.right = insert_trade(node.right, stock_symbol, stop_loss_pct, take_profit_pct)
    return node

# =============================
# Submit Paper Order
# =============================
def submit_paper_order(symbol, side, qty):
    order_data = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=side,
        time_in_force=TimeInForce.DAY
    )
    trading_client.submit_order(order_data)
    print(f"Paper order submitted: {side} {qty} {symbol}")

# =============================
# Fetch Latest Real-Time Prices
# =============================
def fetch_current_prices(stocks):
    current_prices = {}
    request = StockQuotesRequest(symbol_or_symbols=stocks)
    quotes = data_client.get_stock_quotes(request)

    for symbol in stocks:
        current_prices[symbol] = quotes[symbol][-1].ask_price
    return current_prices

# =============================
# Check Trades Function
# =============================
def check_trades(node, current_prices):
    if node is None:
        return

    check_trades(node.left, current_prices)

    current_price = current_prices[node.stock_symbol]

    if current_price <= node.stop_loss:
        print(f"STOP-LOSS triggered: SELL {node.stock_symbol} bought at {node.buy_price}, current price {current_price}")
        submit_paper_order(node.stock_symbol, OrderSide.SELL, 1)
    elif current_price >= node.take_profit:
        print(f"TAKE-PROFIT triggered: SELL {node.stock_symbol} bought at {node.buy_price}, current price {current_price}")
        submit_paper_order(node.stock_symbol, OrderSide.SELL, 1)
    else:
        print(f"HOLD {node.stock_symbol} bought at {node.buy_price}, current price {current_price}")

    check_trades(node.right, current_prices)

# =============================
# Main Program
# =============================
if __name__ == "__main__":
    # Market hours (EST)
    market_open = time(9, 30)
    market_close = time(16, 0)

    # Initialize BST with real-time buy prices
    root = None
    root = insert_trade(root, "GOOGL", stop_loss_pct=0.05, take_profit_pct=0.10)  # 5% SL, 10% TP
    root = insert_trade(root, "AAPL", stop_loss_pct=0.05, take_profit_pct=0.10)
    root = insert_trade(root, "AMZN", stop_loss_pct=0.05, take_profit_pct=0.10)

    stocks = ["GOOGL", "AAPL", "AMZN"]

    print("Starting automated paper trading script with real-time buy prices...")

    while True:
        now = datetime.now().time()
        if market_open <= now <= market_close:
            print(f"\nChecking trades at {datetime.now()}")
            try:
                current_prices = fetch_current_prices(stocks)
                check_trades(root, current_prices)
            except Exception as e:
                print(f"Error fetching prices: {e}")
            t.sleep(3600)  # hourly check
        else:
            print(f"Market is closed at {datetime.now().time()}. Waiting to open...")
            t.sleep(300)  # check every 5 minutes until market opens
