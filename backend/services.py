from yahooquery import Screener, Ticker
from flask import jsonify, request, session
import pandas as pd
from models import User, SavedStocks
from flask_login import current_user
from db import db

def get_popular_stocks():
    """Returns a list of the most active stocks with mini chart data."""
    screener = Screener()
    data = screener.get_screeners('most_actives')

    try:
        stocks_list = data['most_actives']['quotes'][:4]
    except KeyError:
        return jsonify({"error": "Could not retrieve stock data"}), 500

    symbols = [stock.get("symbol") for stock in stocks_list]

    ticker_data = Ticker(symbols)
    hist = ticker_data.history(period="1d", interval="1h")

    mini_chart = {}

    if hist is None or hist.empty:
        for symbol in symbols:
            mini_chart[symbol] = {"timestamps": [], "prices": []}
    else:
        if isinstance(hist.index, pd.MultiIndex):
            grouped = hist.groupby(level=0)
            for symbol, group in grouped:
                group = group.reset_index(level=0, drop=True)
                group.reset_index(inplace=True)
                timestamps = group["date"].astype(str).tolist()
                prices = group["close"].tolist()
                mini_chart[symbol] = {"timestamps": timestamps, "prices": prices}
        else:
            hist.reset_index(inplace=True)
            timestamps = hist["date"].astype(str).tolist()
            prices = hist["close"].tolist()
            mini_chart[symbols[0]] = {"timestamps": timestamps, "prices": prices}

        for symbol in symbols:
            if symbol not in mini_chart:
                mini_chart[symbol] = {"timestamps": [], "prices": []}

    stocks = []
    for stock in stocks_list:
        symbol = stock.get("symbol")
        stock_data = {
            "symbol": symbol,
            "company_name": stock.get("shortName"),
            "current_price": stock.get("regularMarketPrice"),
            "change": stock.get("regularMarketChange"),
            "percent_change": stock.get("regularMarketChangePercent"),
            "mini_chart_data": mini_chart.get(symbol, {"timestamps": [], "prices": []})
        }
        stocks.append(stock_data)

    return jsonify(stocks)

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

def get_save_stock(symbol):

    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'User not logged in'}), 401
    
    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        return jsonify({'success': False, 'error': "User not found"}), 404
    
    existing_stock = SavedStocks.query.filter_by(google_id=google_id, symbol=symbol).first()
    if existing_stock:
        return jsonify({'success': False, 'error': 'Stock is already added'}), 409
    
    stock = Ticker(symbol)
    data = stock.price.get(symbol, {})
    
    new_stock = SavedStocks(
        google_id = google_id,
        symbol = symbol,
        company_name=data.get('shortName') or data.get('longName'),
        price_at_save=data.get('regularMarketPrice'),
    )

    db.session.add(new_stock)
    db.session.commit()


    return jsonify({'success': True, 'message': 'Stock saved successfully!', 'timestamp': new_stock.date_save}) 