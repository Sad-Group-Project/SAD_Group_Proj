from yahooquery import Screener, Ticker
from flask import jsonify, request, session
import pandas as pd
from models import User, SavedStocks
from db import db
import jwt
import os

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

    return stock_data

def get_multiple_stocks(symbols):
    stock_data = {symbol: get_stocks(symbol) for symbol in symbols}
    return stock_data

def get_add_stock(symbol, SECRET_KEY):
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"success": False, "error": "Missing or invalid token"}), 401

    token = auth_header.split(" ")[1]

    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        google_id = decoded_token.get("google_id")
    except jwt.ExpiredSignatureError:
        return jsonify({"success": False, "error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"success": False, "error": "Invalid token"}), 401

    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    existing_stock = SavedStocks.query.filter_by(google_id=google_id, symbol=symbol).first()
    if existing_stock:
        return jsonify({"success": False, "error": "Stock is already added"}), 409

    stock = Ticker(symbol)
    data = stock.price.get(symbol, {})

    new_stock = SavedStocks(
        google_id=google_id,
        symbol=symbol,
        company_name=data.get("shortName") or data.get("longName"),
        price_at_save=data.get("regularMarketPrice"),
    )

    db.session.add(new_stock)
    db.session.commit()

    return jsonify({"success": True, "message": "Stock saved successfully!", "timestamp": new_stock.date_save})

def get_users_stocks(SECRET_KEY):
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"success": False, "error": "Missing or invalid token"}), 401
    
    token = auth_header.split(" ")[1]
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        google_id = decoded_token.get("google_id")
    except jwt.ExpiredSignatureError:
        return jsonify({"success": False, "error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"success": False, "error": "Invalid token"}), 401
    
    saved_stocks = SavedStocks.query.filter_by(google_id=google_id).all()

    stock_symbols = [stock.symbol for stock in saved_stocks]

    stocks_data = get_multiple_stocks(stock_symbols)

    saved_stocks_list = [
        {
            "symbol": stock.symbol,
            "company_name": stock.company_name,
            "price_at_save": stock.price_at_save,
            "date_saved": stock.date_save,
            "current_info": stocks_data.get(stock.symbol, {})
        }
        for stock in saved_stocks
    ]

    return jsonify({"success": True, "saved_stocks": saved_stocks_list})

def get_user_profile(SECRET_KEY):
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"success": False, "error": "Missing or invalid token"}), 401
    
    token = auth_header.split(" ")[1]

    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        google_id = decoded_token.get("google_id")
    except jwt.ExpiredSignatureError:
        return jsonify({"success": False, "error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"success": False, "error": "Invalid token"}), 401
    
    user_profile = User.query.filter_by(google_id=google_id).first()

    user_info = {
        "google_id": user_profile.google_id,
        "username": user_profile.name,
        "email": user_profile.email,
        "profile_picture": user_profile.profile_picture,
        "created_at": user_profile.created_at
    }

    return jsonify(user_info)