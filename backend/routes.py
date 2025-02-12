from flask import Blueprint, jsonify, request
from yahooquery import Screener, Ticker
api = Blueprint('api', __name__)

def get_mini_chart(symbol):
    """Fetches intraday stock prices for a small chart visualization."""
    stock = Ticker(symbol)
    hist = stock.history(period="1d", interval="1h")

    if hist.empty:
        return {"timestamps": [], "prices": []}

    hist.reset_index(inplace=True)
    timestamps = hist["date"].astype(str).tolist()
    prices = hist["close"].tolist()

    return {"timestamps": timestamps, "prices": prices}

@api.route('/popular_stocks', methods=['GET'], strict_slashes=False)
def popular_stocks():
    """Returns a list of the most active stocks with mini chart data."""
    screener = Screener()
    
    data = screener.get_screeners('most_actives')

    try:
        stocks_list = data['most_actives']['quotes'][:4]
    except KeyError:
        return jsonify({"error": "Could not retrieve stock data"}), 500

    stocks = []
    for stock in stocks_list:
        stock_data = {
            "symbol": stock.get("symbol"),
            "company_name": stock.get("shortName"),
            "current_price": stock.get("regularMarketPrice"),
            "change": stock.get("regularMarketChange"),
            "percent_change": stock.get("regularMarketChangePercent"),
            "mini_chart_data": get_mini_chart(stock.get("symbol"))
        }
        stocks.append(stock_data)

    return jsonify(stocks)

@api.route('/debug')
def debug():
    return jsonify({
        'url': request.url,
        'scheme': request.scheme,
        'headers': dict(request.headers)
    })

@api.route('/test')
def test():
    return "HELLO"