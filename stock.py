# =============================
# stock.py
# =============================
import os
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.requests import StockQuotesRequest
from alpaca.data.historical import StockHistoricalDataClient

# =============================
# Load API keys from GitHub secrets
# =============================
API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_SECRET_KEY")

print("DEBUG:")
print("API key exists:", API_KEY is not None)
print("Secret key exists:", API_SECRET is not None)

if not API_KEY or not API_SECRET:
    raise ValueError("ALPACA_API_KEY or ALPACA_SECRET_KEY not set!")

# =============================
# Initialize trading client (paper account)
# =============================
trading_client = TradingClient(API_KEY, API_SECRET, paper=True)

# =============================
# BST Node class
# =============================
class Node:
    def __init__(self, stock_symbol):
        self.stock_symbol = stock_symbol
        self.buy_price = 0.0
        self.stop_loss = 0.0
        self.take_profit = 0.0
        self.shares_held = 0
        self.left = None
        self.right = None

# =============================
# Insert stock into BST
# =============================
def insert_trade(node, stock_symbol):
    if node is None:
        return Node(stock_symbol)
    if stock_symbol < node.stock_symbol:
        node.left = insert_trade(node.left, stock_symbol)
    else:
        node.right = insert_trade(node.right, stock_symbol)
    return node

# =============================
# Fetch current stock prices
# =============================
def fetch_current_prices(stocks):
    current_prices = {}
    request = StockQuotesRequest(symbol_or_symbols=stocks)
    quotes = StockHistoricalDataClient(API_KEY, API_SECRET).get_stock_quotes(request)
    for symbol in stocks:
        current_prices[symbol] = quotes[symbol][-1].ask_price
    return current_prices

# =============================
# Buy shares function
# =============================
def buy_stock(symbol, qty):
    order_data = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY
    )
    trading_client.submit_order(order_data)
    print(f"Paper BUY order submitted: {qty} shares of {symbol}")
    return qty

# =============================
# Check trades function with max shares limit
# =============================
MAX_SHARES = 80

def check_trades(node, current_prices, shares_to_buy):
    if node is None:
        return

    check_trades(node.left, current_prices, shares_to_buy)

    current_price = current_prices[node.stock_symbol]

    # Buy more shares only if under MAX_SHARES
    if node.shares_held < MAX_SHARES:
        shares_to_add = min(shares_to_buy, MAX_SHARES - node.shares_held)
        if shares_to_add > 0:
            node.shares_held += buy_stock(node.stock_symbol, shares_to_add)
            node.buy_price = current_price
            node.stop_loss = node.buy_price * 0.95
            node.take_profit = node.buy_price * 1.10

    # Check stop-loss
    if node.shares_held > 0 and current_price <= node.stop_loss:
        print(f"STOP-LOSS triggered: SELL {node.stock_symbol} bought at {node.buy_price}, current price {current_price}")
        order_data = MarketOrderRequest(
            symbol=node.stock_symbol,
            qty=node.shares_held,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY
        )
        trading_client.submit_order(order_data)
        node.shares_held = 0

    # Check take-profit
    elif node.shares_held > 0 and current_price >= node.take_profit:
        print(f"TAKE-PROFIT triggered: SELL {node.stock_symbol} bought at {node.buy_price}, current price {current_price}")
        order_data = MarketOrderRequest(
            symbol=node.stock_symbol,
            qty=node.shares_held,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY
        )
        trading_client.submit_order(order_data)
        node.shares_held = 0

    else:
        print(f"HOLD {node.stock_symbol}: bought at {node.buy_price}, current price {current_price}, shares held: {node.shares_held}")

    check_trades(node.right, current_prices, shares_to_buy)

# =============================
# Main execution
# =============================
if __name__ == "__main__":
    root = None
    root = insert_trade(root, "GOOGL")
    root = insert_trade(root, "AAPL")
    root = insert_trade(root, "AMZN")

    stocks = ["GOOGL", "AAPL", "AMZN"]
    shares_to_buy = 50  # number of shares to attempt buying per run

    print("Running Stock Bot once for GitHub Actions...")
    try:
        current_prices = fetch_current_prices(stocks)
        check_trades(root, current_prices, shares_to_buy)
    except Exception as e:
        print(f"Error running bot: {e}")

    print("Stock Bot run complete. Exiting.")
