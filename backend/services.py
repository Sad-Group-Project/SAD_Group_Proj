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

    stock_data = []

    for symbol in symbols:
        stock_history = close_prices[close_prices['symbol'] == symbol]

        labels = stock_history['date'].astype(str).tolist()
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

    search_data = []

    for value in results.get('quotes', []):
        temp = {
            'symbol': value.get('symbol', 'Unknown'),
            'longname': value.get('longname', 'Unknown'),
            'shortname': value.get('shortname', 'Unkown'),
            'exchange': value.get('exchange', 'Unkown'),
            "exchDisp": value.get('exchDisp', 'Unkown'),
            "industry": value.get('industry', 'Unknown'),
        }
        search_data.append(temp)
    # return results
    return jsonify({'quotes': search_data})



