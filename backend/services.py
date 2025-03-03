from yahooquery import Screener, Ticker, search
from flask import jsonify
import pandas as pd

def get_popular_stocks():
    screener = Screener()
    data = screener.get_screeners('most_actives')

    try:
        stocks_list = data['most_actives']['quotes'][:4]
    except KeyError:
        return jsonify({"error": "Could not retrieve stock data"}), 500

    symbols = [stock.get("symbol") for stock in stocks_list]
    stock_names = {stock.get("symbol"): stock.get("shortName", stock.get("symbol")) for stock in stocks_list}

    ticker_data = Ticker(symbols)
    history = ticker_data.history(period="5d", interval="1d")

    close_prices = history[['close']].reset_index()

    close_prices['date'] = pd.to_datetime(close_prices['date'], utc=True).dt.tz_localize(None)

    stock_data = []

    for symbol in symbols:
        stock_history = close_prices[close_prices['symbol'] == symbol]

        labels = stock_history['date'].dt.strftime('%Y-%m-%d').tolist()
        values = stock_history['close'].tolist()

        stock_data.append({
            "name": stock_names.get(symbol, symbol),
            "ticker": symbol,
            "chartData": {
                "labels": labels,
                "values": values
            }
        })

    return jsonify(stock_data)


def get_stocks(user_search):

    stock_symbol = user_search.upper()
    searchedStock = Ticker(user_search)
    results = searchedStock.financial_data
    stock_info = results.get(stock_symbol, {})

    history_data = searchedStock.history(period="1mo")

    history = []
    stock_price = stock_info.get("currentPrice")
    price_24h_ago = None

    if isinstance(history_data, pd.DataFrame) and not history_data.empty:
        history_data = history_data.reset_index()

        if len(history_data) > 1:
            price_24h_ago = history_data.iloc[-2]["close"]

        history = [
            {"date": row["date"].strftime("%Y-%m-%d"), "price": row["close"]}
            for _, row in history_data.iterrows()
        ]

    price_change = stock_price - price_24h_ago
    price_change_percentage = (price_change / price_24h_ago) * 100

    stock_data = {
        'symbol': stock_symbol,
        'price': stock_price,
        'recommendation': stock_info.get("recommendationKey"),
        'change': price_change_percentage,
        'history': history
    }

    return jsonify(stock_data)

def get_search(user_search):
    results = search(user_search)
    symbols = [value.get('symbol', 'Unknown') for value in results.get('quotes', [])]

    if not symbols:
        return jsonify({'quotes': []}) 

    stock_data = Ticker(symbols)

    price_data = stock_data.price
    history_data = stock_data.history(period="1d", interval="1h")

    search_data = []

    for value in results.get('quotes', []):
        symbol = value.get('symbol', 'Unknown')

        price_info = price_data.get(symbol, {})
        stock_price = price_info.get("regularMarketPrice", 0.00)
        previous_close = price_info.get("regularMarketPreviousClose", stock_price)

        price_change_percent = round(((stock_price - previous_close) / previous_close) * 100, 2) if previous_close else 0.00

        chart_data = []
        if isinstance(history_data, pd.DataFrame) and not history_data.empty and symbol in history_data.index:
            stock_history = history_data.xs(symbol, level=0)
            chart_data = stock_history["close"].dropna().tolist()

        temp = {
            "symbol": symbol,
            "longName": value.get("longname", "Unknown"),
            "shortName": value.get("shortname", "Unknown"),
            "exchange": value.get("exchange", "Unknown"),
            "exchDisp": value.get("exchDisp", "Unknown"),
            "industry": value.get("industry", "Unknown"),
            "regularMarketPrice": stock_price,
            "regularMarketChangePercent": price_change_percent,
            "chartData": chart_data if chart_data else [0]
        }

        search_data.append(temp)

    return jsonify({'quotes': search_data})