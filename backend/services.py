from yahooquery import Screener, Ticker, search
from flask import jsonify, request, session
import pandas as pd
from models import User, SavedStocks
from db import db
import jwt
import os
import re
import time
import random
import yfinance as yf
from sqlalchemy.exc import IntegrityError

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
                timestamps = group["date"].dt.strftime("%Y-%m-%dT%H:%M:%S").tolist()
                prices = group["close"].tolist()
                mini_chart[symbol] = {"timestamps": timestamps, "prices": prices}
        else:
            hist.reset_index(inplace=True)
            timestamps = hist["date"].dt.strftime("%Y-%m-%dT%H:%M:%S").tolist()
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
    tickers = Ticker(symbols, asynchronous=True)

    financials = tickers.financial_data
    history_data = tickers.history(period="1mo")

    stock_data = {}

    for symbol in symbols:
        info = financials.get(symbol, {})
        history_df = history_data.loc[symbol] if isinstance(history_data, pd.DataFrame) and symbol in history_data.index else pd.DataFrame()

        history = []
        stock_price = info.get("currentPrice")
        price_24h_ago = None

        if not history_df.empty:
            history_df = history_df.reset_index()
            if len(history_df) > 1:
                price_24h_ago = history_df.iloc[-2]["close"]

            history = [
                {"date": row["date"].strftime("%Y-%m-%d"), "price": row["close"]}
                for _, row in history_df.iterrows()
            ]

        price_change = 0
        price_change_percentage = 0

        if stock_price and price_24h_ago:
            price_change = stock_price - price_24h_ago
            price_change_percentage = (price_change / price_24h_ago) * 100

        stock_data[symbol] = {
            'symbol': symbol,
            'price': stock_price,
            'recommendation': info.get("recommendationKey"),
            'change': price_change_percentage,
            'history': history
        }

    return stock_data


def get_add_stock(symbol, SECRET_KEY):
    if not symbol or symbol.upper() in ["", "EMPTY", "NONE"] or not re.match(r"^[A-Z.\-]+$", symbol.upper()):
        return jsonify({"success": False, "error": "Invalid stock symbol"}), 400

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

    company_name = data.get("shortName") or data.get("longName")
    price_at_save = data.get("regularMarketPrice")

    if not company_name or price_at_save is None:
        return jsonify({"success": False, "error": "Invalid or missing stock data"}), 400

    new_stock = SavedStocks(
        google_id=google_id,
        symbol=symbol,
        company_name=company_name,
        price_at_save=price_at_save,
    )

    try:
        db.session.add(new_stock)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"success": False, "error": "Stock already exists"}), 409

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

def remove_stock(stock_symbol, SECRET_KEY):
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
    
    stock = SavedStocks.query.filter_by(google_id=google_id, symbol=stock_symbol).first()
    if stock:
        db.session.delete(stock)
        db.session.commit()
        return {'message': f'{stock_symbol} deleted'}
    else:
        return {'error': 'Stock not found'}, 404

def get_detailed_stock_info(stock_symbol):
    if not stock_symbol or not isinstance(stock_symbol, str):
        return jsonify({"success": False, "error": "Invalid stock symbol"}), 400

    symbol = stock_symbol.upper()
    
    try:
        detailed_data = {
            "success": True,
            "symbol": symbol,
            "company_info": {
                "name": symbol,
                "sector": "",
                "industry": "",
                "website": "",
                "description": "",
                "exchange": "",
                "market_cap": 0,
                "employees": 0
            },
            "price_data": {
                "current_price": 0,
                "previous_close": 0,
                "open": 0,
                "day_high": 0,
                "day_low": 0,
                "day_change": 0,
                "day_change_percent": 0,
                "52wk_high": 0,
                "52wk_low": 0,
                "volume": 0
            },
            "financial_metrics": {
                "pe_ratio": 0,
                "eps": 0,
                "dividend_yield": 0,
                "dividend_rate": 0,
                "profit_margin": 0,
                "beta": 0,
                "recommendation": "NONE",
                "target_price": 0
            },
            "historical_data": {
                "1d": {"interval": "15m", "data": []},
                "1mo": {"interval": "1d", "data": []},
                "1y": {"interval": "1wk", "data": []},
                "5y": {"interval": "1mo", "data": []}
            }
        }
        
        stock = yf.Ticker(symbol)
        
        try:
            fast_info = stock.fast_info
            if fast_info:
                
                current_price = getattr(fast_info, 'last_price', None) or getattr(fast_info, 'regularMarketPrice', 0)
                previous_close = getattr(fast_info, 'previous_close', current_price)
                
                if current_price and previous_close:
                    day_change = current_price - previous_close
                    day_change_percent = (day_change / previous_close) * 100 if previous_close else 0
                    
                    detailed_data["price_data"].update({
                        "current_price": current_price,
                        "previous_close": previous_close, 
                        "open": getattr(fast_info, 'open', current_price),
                        "day_high": getattr(fast_info, 'day_high', current_price),
                        "day_low": getattr(fast_info, 'day_low', current_price),
                        "day_change": day_change,
                        "day_change_percent": day_change_percent,
                        "volume": getattr(fast_info, 'last_volume', 0) or 0
                    })
                
                detailed_data["price_data"]["52wk_high"] = getattr(fast_info, 'year_high', 0) or 0
                detailed_data["price_data"]["52wk_low"] = getattr(fast_info, 'year_low', 0) or 0
                
                if hasattr(fast_info, 'market_cap') and fast_info.market_cap:
                    detailed_data["company_info"]["market_cap"] = fast_info.market_cap
        except Exception as e:
            print(f"Error fetching fast info: {str(e)}")

        try:
            info = stock.info
            
            if info:
                detailed_data["company_info"].update({
                    "name": info.get("shortName") or info.get("longName") or symbol,
                    "sector": info.get("sector", ""),
                    "industry": info.get("industry", ""),
                    "website": info.get("website", ""),
                    "description": info.get("longBusinessSummary", ""),
                    "exchange": info.get("exchange", ""),
                    "employees": info.get("fullTimeEmployees", 0) or 0
                })
                
                if not detailed_data["company_info"]["market_cap"] and info.get("marketCap"):
                    detailed_data["company_info"]["market_cap"] = info.get("marketCap")
                
                if not detailed_data["price_data"]["current_price"] and info.get("currentPrice"):
                    current_price = info.get("currentPrice")
                    previous_close = info.get("previousClose", current_price)
                    
                    if current_price and previous_close:
                        day_change = current_price - previous_close
                        day_change_percent = (day_change / previous_close) * 100 if previous_close else 0
                        
                        if not detailed_data["price_data"]["current_price"]:
                            detailed_data["price_data"]["current_price"] = current_price
                        if not detailed_data["price_data"]["previous_close"]:
                            detailed_data["price_data"]["previous_close"] = previous_close
                        if not detailed_data["price_data"]["open"]:
                            detailed_data["price_data"]["open"] = info.get("open", current_price)
                        if not detailed_data["price_data"]["day_high"]:
                            detailed_data["price_data"]["day_high"] = info.get("dayHigh", current_price)
                        if not detailed_data["price_data"]["day_low"]:
                            detailed_data["price_data"]["day_low"] = info.get("dayLow", current_price)
                        if not detailed_data["price_data"]["day_change"]:
                            detailed_data["price_data"]["day_change"] = day_change
                        if not detailed_data["price_data"]["day_change_percent"]:
                            detailed_data["price_data"]["day_change_percent"] = day_change_percent
                
                if not detailed_data["price_data"]["52wk_high"]:
                    detailed_data["price_data"]["52wk_high"] = info.get("fiftyTwoWeekHigh", 0)
                if not detailed_data["price_data"]["52wk_low"]:
                    detailed_data["price_data"]["52wk_low"] = info.get("fiftyTwoWeekLow", 0)
                
                if not detailed_data["price_data"]["volume"]:
                    detailed_data["price_data"]["volume"] = info.get("volume", 0) or info.get("averageVolume", 0) or 0
                
                detailed_data["financial_metrics"].update({
                    "pe_ratio": info.get("forwardPE", 0) or info.get("trailingPE", 0) or 0,
                    "eps": info.get("trailingEps", 0) or 0,
                    "dividend_yield": (info.get("dividendYield", 0) or 0) * 100,
                    "dividend_rate": info.get("dividendRate", 0) or 0,
                    "profit_margin": info.get("profitMargins", 0) or 0,
                    "beta": info.get("beta", 0) or 0,
                    "recommendation": info.get("recommendationKey", "NONE") or "NONE",
                    "target_price": info.get("targetMeanPrice", 0) or 0
                })
        except Exception as e:
            print(f"Error fetching company info: {str(e)}")
        
        timeframes = {
            "1d": {"period": "1d", "interval": "15m"},
            "1mo": {"period": "1mo", "interval": "1d"},
            "1y": {"period": "1y", "interval": "1wk"},
            "5y": {"period": "5y", "interval": "1mo"}
        }
        
        for timeframe, params in timeframes.items():
            try:
                history = stock.history(period=params["period"], interval=params["interval"])
                
                if not history.empty:
                    data_points = []
                    
                    for date, row in history.iterrows():
                        if isinstance(date, pd.Timestamp):
                            timestamp = int(date.timestamp() * 1000)
                        else:
                            timestamp = int(pd.Timestamp(date).timestamp() * 1000)
                        
                        if isinstance(row, pd.Series) and "Close" in row:
                            close_price = row["Close"]
                        elif isinstance(row, pd.DataFrame):
                            if "Close" in row.columns:
                                close_price = row["Close"].iloc[0]
                            else:
                                close_price = 0
                        else:
                            close_price = 0
                        
                        data_points.append({
                            "timestamp": timestamp,
                            "value": float(close_price),
                            "date": date.strftime("%Y-%m-%d %H:%M:%S") if hasattr(date, "strftime") else str(date),
                            "close": float(close_price)
                        })
                    
                    data_points.sort(key=lambda x: x["timestamp"])
                    
                    detailed_data["historical_data"][timeframe]["data"] = data_points
                    
                else:
                    print(f"No historical data returned for {timeframe}")
            except Exception as e:
                print(f"Error fetching {timeframe} history for {symbol}: {str(e)}")
        
        return jsonify(detailed_data)
    
    except Exception as e:
        error_response = {
            "success": True,
            "symbol": symbol,
            "error_info": str(e),
            "company_info": {"name": symbol, "sector": "", "industry": "", "exchange": "", "market_cap": 0, "employees": 0},
            "price_data": {
                "current_price": 0, "previous_close": 0, "open": 0,
                "day_high": 0, "day_low": 0, "day_change": 0, "day_change_percent": 0,
                "52wk_high": 0, "52wk_low": 0, "volume": 0
            },
            "financial_metrics": {
                "pe_ratio": 0, "eps": 0, "dividend_yield": 0, 
                "dividend_rate": 0, "profit_margin": 0, "beta": 0,
                "recommendation": "NONE", "target_price": 0
            },
            "historical_data": {
                "1d": {"interval": "15m", "data": []},
                "1mo": {"interval": "1d", "data": []},
                "1y": {"interval": "1wk", "data": []},
                "5y": {"interval": "1mo", "data": []}
            }
        }
        return jsonify(error_response)
