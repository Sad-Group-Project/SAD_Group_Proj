from flask import jsonify, request, session
import pandas as pd
from models import User, SavedStocks
from db import db
import jwt
import os
import re
import time
import random
import requests
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from functools import wraps
from cachelib.simple import SimpleCache

cache = SimpleCache(threshold=500, default_timeout=300)

def cached(key_prefix):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = key_prefix
            if args:
                cache_key += "_" + "_".join(str(arg) for arg in args)
            if kwargs:
                cache_key += "_" + "_".join(f"{k}_{v}" for k, v in sorted(kwargs.items()))
            
            rv = cache.get(cache_key)
            if rv is not None:
                return rv
            
            rv = f(*args, **kwargs)
            
            cache.set(cache_key, rv)
            return rv
        return decorated_function
    return decorator

@cached("popular_stocks")
def get_popular_stocks():
    """Returns a list of the most active stocks with mini chart data."""
    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return jsonify({"error": "API key not configured"}), 500
        
    try:
        active_url = f"https://financialmodelingprep.com/api/v3/stock_market/actives?apikey={api_key}"
        active_response = requests.get(active_url)
        active_stocks = active_response.json()
        
        if not active_stocks or not isinstance(active_stocks, list):
            return jsonify({"error": "Could not retrieve active stocks"}), 500
            
        active_stocks = active_stocks[4:8]
        
        stocks_list = []
        symbols = [stock.get('symbol') for stock in active_stocks]
        
        for stock_data in active_stocks:
            symbol = stock_data.get('symbol')
            
            mini_chart_data = {"timestamps": [], "prices": []}
            try:
                chart_url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?from={(datetime.now() - timedelta(days=56)).strftime('%Y-%m-%d')}&to={datetime.now().strftime('%Y-%m-%d')}&apikey={api_key}"
                chart_response = requests.get(chart_url)
                chart_data = chart_response.json()
                
                if chart_data and "historical" in chart_data and isinstance(chart_data["historical"], list):
                    timestamps = []
                    prices = []
                    
                    weekly_data = []
                    current_week = -1
                    
                    sorted_data = sorted(chart_data["historical"], key=lambda x: x.get("date", ""), reverse=True)
                    
                    for item in sorted_data:
                        date_str = item.get("date", "")
                        try:
                            dt = datetime.strptime(date_str, "%Y-%m-%d")
                            week_number = dt.isocalendar()[1]
                            
                            if week_number != current_week and len(weekly_data) < 8:
                                current_week = week_number
                                weekly_data.append(item)
                        except Exception as e:
                            print(f"Error processing date {date_str} for {symbol}: {str(e)}")
                    
                    for item in reversed(weekly_data):
                        date_str = item.get("date", "")
                        timestamps.append(date_str)
                        prices.append(item.get("close", 0))
                            
                    mini_chart_data = {"timestamps": timestamps, "prices": prices}
            except Exception as e:
                print(f"Error fetching chart data for {symbol}: {str(e)}")
            
            stock_info = {
                "symbol": symbol,
                "company_name": stock_data.get("name", symbol),
                "current_price": stock_data.get("price", 0),
                "change": stock_data.get("change", 0),
                "percent_change": stock_data.get("changesPercentage", 0),
                "mini_chart_data": mini_chart_data
            }
            
            stocks_list.append(stock_info)
        
        return jsonify(stocks_list)
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve stock data: {str(e)}"}), 500

@cached("stocks")
def get_stocks(user_search):
    if not user_search:
        return {
            'symbol': '',
            'price': 0,
            'recommendation': None,
            'change': 0,
            'history': []
        }
        
    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return {
            'symbol': user_search.upper(),
            'price': 0,
            'recommendation': None,
            'change': 0,
            'history': []
        }
        
    symbol = user_search.upper()
    
    try:
        quote_url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={api_key}"
        quote_response = requests.get(quote_url)
        quote_data = quote_response.json()
        
        if not quote_data or not isinstance(quote_data, list) or len(quote_data) == 0:
            return {
                'symbol': symbol,
                'price': 0,
                'recommendation': None,
                'change': 0,
                'history': []
            }
        
        stock_price = quote_data[0].get('price', 0)
        change_percentage = quote_data[0].get('changesPercentage', 0)
        
        history_url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?timeseries=30&apikey={api_key}"
        history_response = requests.get(history_url)
        history_data = history_response.json()
        
        history_list = []
        if 'historical' in history_data:
            for item in history_data['historical'][:30]:
                history_list.append({
                    "date": item.get("date", ""),
                    "price": item.get("close", 0)
                })
        
        recommendation = "NONE"
        rating_url = f"https://financialmodelingprep.com/api/v3/rating/{symbol}?apikey={api_key}"
        try:
            rating_response = requests.get(rating_url)
            rating_data = rating_response.json()
            if rating_data and isinstance(rating_data, list) and len(rating_data) > 0:
                recommendation = rating_data[0].get('ratingRecommendation', 'NONE')
                
        except Exception as e:
            print(f"Error fetching rating for {symbol}: {str(e)}")
            
        stock_data = {
            'symbol': symbol,
            'price': stock_price,
            'recommendation': recommendation,
            'change': change_percentage,
            'history': history_list
        }
        
        return stock_data
    except Exception as e:
        print(f"Error fetching stock data: {str(e)}")
        return {
            'symbol': user_search.upper(),
            'price': 0,
            'recommendation': None,
            'change': 0,
            'history': []
        }

@cached("multiple_stocks")
def get_multiple_stocks(symbols):
    if not symbols:
        return {}
        
    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return {symbol: {
            'symbol': symbol,
            'price': 0,
            'recommendation': None,
            'change': 0,
            'history': []
        } for symbol in symbols}
        
    url = f"https://financialmodelingprep.com/api/v3/quote/{','.join(symbols)}?apikey={api_key}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if not data or not isinstance(data, list):
            return {symbol: {
                'symbol': symbol,
                'price': 0,
                'recommendation': None,
                'change': 0,
                'history': []
            } for symbol in symbols}
        
        stock_data = {}
        
        for quote in data:
            symbol = quote.get('symbol')
            
            history_url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?timeseries=30&apikey={api_key}"
            history_response = requests.get(history_url)
            history_data = history_response.json()
            
            history_list = []
            if 'historical' in history_data:
                for item in history_data['historical'][:30]:
                    history_list.append({
                        "date": item.get("date", ""),
                        "price": item.get("close", 0)
                    })
            
            stock_price = quote.get('price', 0)
            change_percentage = quote.get('changesPercentage', 0)
            
            recommendation = "NONE"
            rating_url = f"https://financialmodelingprep.com/api/v3/rating/{symbol}?apikey={api_key}"
            try:
                rating_response = requests.get(rating_url)
                rating_data = rating_response.json()
                if rating_data and isinstance(rating_data, list) and len(rating_data) > 0:
                    recommendation = rating_data[0].get('ratingRecommendation', 'NONE')
                    
            except Exception as e:
                print(f"Error fetching rating for {symbol}: {str(e)}")
                
            stock_data[symbol] = {
                'symbol': symbol,
                'price': stock_price,
                'recommendation': recommendation,
                'change': change_percentage,
                'history': history_list
            }
        
        return stock_data
    except Exception as e:
        print(f"Error fetching multiple stocks: {str(e)}")
        return {symbol: {
            'symbol': symbol,
            'price': 0,
            'recommendation': None,
            'change': 0,
            'history': []
        } for symbol in symbols}

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

    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return jsonify({"success": False, "error": "API key not configured"}), 500
        
    url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={api_key}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if not data or not isinstance(data, list) or len(data) == 0:
            return jsonify({"success": False, "error": "Invalid or missing stock data"}), 400
            
        quote = data[0]
        company_name = quote.get("name") or symbol
        price_at_save = quote.get("price")
        
        if not price_at_save:
            return jsonify({"success": False, "error": "Invalid or missing stock price data"}), 400

        new_stock = SavedStocks(
            google_id=google_id,
            symbol=symbol,
            company_name=company_name,
            price_at_save=price_at_save,
        )

        db.session.add(new_stock)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"success": False, "error": "Stock already exists"}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to save stock: {str(e)}"}), 500

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
    if not user_search:
        return jsonify({'quotes': []})
        
    api_key = os.environ.get("FMP_API_KEY")
    if not api_key:
        return jsonify({'quotes': []})
    
    try:
        search_url = f"https://financialmodelingprep.com/api/v3/search?query={user_search}&limit=10&apikey={api_key}"
        search_response = requests.get(search_url)
        search_results = search_response.json()
        
        if not search_results or not isinstance(search_results, list):
            return jsonify({'quotes': []})
            
        symbols = [item.get('symbol') for item in search_results if item.get('symbol')]
        
        if not symbols:
            return jsonify({'quotes': []})
            
        quotes_url = f"https://financialmodelingprep.com/api/v3/quote/{','.join(symbols)}?apikey={api_key}"
        quotes_response = requests.get(quotes_url)
        quotes_data = quotes_response.json()
        
        if not quotes_data or not isinstance(quotes_data, list):
            return jsonify({'quotes': []})
            
        quotes_map = {quote.get('symbol'): quote for quote in quotes_data}
        
        search_data = []
        
        for item in search_results:
            symbol = item.get('symbol')
            if not symbol or symbol not in quotes_map:
                continue
                
            quote = quotes_map[symbol]
            
            chart_data = []
            try:
                chart_url = f"https://financialmodelingprep.com/api/v3/historical-chart/1hour/{symbol}?apikey={api_key}"
                chart_response = requests.get(chart_url)
                chart_results = chart_response.json()
                
                if chart_results and isinstance(chart_results, list):
                    chart_data = [item.get('close', 0) for item in chart_results][::-1]
            except Exception as e:
                print(f"Error fetching chart data for {symbol}: {str(e)}")
                
            temp = {
                "symbol": symbol,
                "longName": item.get("name", "Unknown"),
                "shortName": item.get("name", "Unknown"),
                "exchange": item.get("exchangeShortName", "Unknown"),
                "exchDisp": item.get("stockExchange", "Unknown"),
                "industry": quote.get("industry", "Unknown"),
                "regularMarketPrice": quote.get("price", 0.00),
                "regularMarketChangePercent": quote.get("changesPercentage", 0.00),
                "chartData": chart_data if chart_data else [0]
            }
            
            search_data.append(temp)
            
        return jsonify({'quotes': search_data})
        
    except Exception as e:
        print(f"Error in search: {str(e)}")
        return jsonify({'quotes': []})

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
    api_key = os.environ.get("FMP_API_KEY")
    
    if not api_key:
        return jsonify({
            "success": False, 
            "error": "API key not configured", 
            "symbol": symbol
        }), 500
    
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
        
        quote_url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={api_key}"
        quote_response = requests.get(quote_url)
        quote_data = quote_response.json()
        
        if quote_data and isinstance(quote_data, list) and len(quote_data) > 0:
            quote = quote_data[0]
            current_price = quote.get("price", 0)
            previous_close = quote.get("previousClose", current_price)
            
            if current_price and previous_close:
                day_change = current_price - previous_close
                day_change_percent = (day_change / previous_close) * 100 if previous_close else 0
                
                detailed_data["price_data"].update({
                    "current_price": current_price,
                    "previous_close": previous_close,
                    "open": quote.get("open", current_price),
                    "day_high": quote.get("dayHigh", current_price),
                    "day_low": quote.get("dayLow", current_price),
                    "day_change": day_change,
                    "day_change_percent": day_change_percent,
                    "volume": quote.get("volume", 0),
                    "52wk_high": quote.get("yearHigh", 0),
                    "52wk_low": quote.get("yearLow", 0)
                })
        
        profile_url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={api_key}"
        profile_response = requests.get(profile_url)
        profile_data = profile_response.json()
        
        if profile_data and isinstance(profile_data, list) and len(profile_data) > 0:
            profile = profile_data[0]
            
            detailed_data["company_info"].update({
                "name": profile.get("companyName") or symbol,
                "sector": profile.get("sector", ""),
                "industry": profile.get("industry", ""),
                "website": profile.get("website", ""),
                "description": profile.get("description", ""),
                "exchange": profile.get("exchange", ""),
                "market_cap": profile.get("mktCap", 0),
                "employees": profile.get("fullTimeEmployees", 0)
            })
            
            beta = profile.get("beta", 0)
            
            if not detailed_data["price_data"]["volume"]:
                detailed_data["price_data"]["volume"] = profile.get("volume", 0)
                
            if not detailed_data["price_data"]["52wk_high"]:
                detailed_data["price_data"]["52wk_high"] = profile.get("yearHigh", 0)
                
            if not detailed_data["price_data"]["52wk_low"]:
                detailed_data["price_data"]["52wk_low"] = profile.get("yearLow", 0)
                
            current_price = detailed_data["price_data"]["current_price"] or profile.get("price", 0)
            div_yield = 0
            if profile.get("lastDiv", 0) > 0 and current_price > 0:
                div_yield = (profile.get("lastDiv", 0) / current_price) * 100
                
            detailed_data["financial_metrics"].update({
                "pe_ratio": profile.get("pe", 0),
                "eps": profile.get("eps", 0),
                "dividend_yield": div_yield,
                "dividend_rate": profile.get("lastDiv", 0),
                "profit_margin": profile.get("profitMargin", 0),
                "beta": beta
            })
            
        key_metrics_url = f"https://financialmodelingprep.com/api/v3/key-metrics/{symbol}?limit=1&apikey={api_key}"
        key_metrics_response = requests.get(key_metrics_url)
        key_metrics_data = key_metrics_response.json()
        
        if key_metrics_data and isinstance(key_metrics_data, list) and len(key_metrics_data) > 0:
            metrics = key_metrics_data[0]
            
            if not detailed_data["financial_metrics"]["pe_ratio"] or detailed_data["financial_metrics"]["pe_ratio"] == 0:
                detailed_data["financial_metrics"]["pe_ratio"] = metrics.get("peRatio", 0) or 0
                
            if not detailed_data["financial_metrics"]["eps"] or detailed_data["financial_metrics"]["eps"] == 0:
                detailed_data["financial_metrics"]["eps"] = metrics.get("netIncomePerShare", 0) or 0
                
            if not detailed_data["financial_metrics"]["profit_margin"] or detailed_data["financial_metrics"]["profit_margin"] == 0:
                detailed_data["financial_metrics"]["profit_margin"] = metrics.get("netProfitMargin", 0) or 0
        
        ratios_url = f"https://financialmodelingprep.com/api/v3/ratios/{symbol}?limit=1&apikey={api_key}"
        ratios_response = requests.get(ratios_url)
        ratios_data = ratios_response.json()
        
        if ratios_data and isinstance(ratios_data, list) and len(ratios_data) > 0:
            ratios = ratios_data[0]
            
            if not detailed_data["financial_metrics"]["pe_ratio"] or detailed_data["financial_metrics"]["pe_ratio"] == 0:
                detailed_data["financial_metrics"]["pe_ratio"] = ratios.get("priceEarningsRatio", 0) or 0
                
            if not detailed_data["financial_metrics"]["eps"] or detailed_data["financial_metrics"]["eps"] == 0:
                eps_ttm = ratios.get("priceToBookRatio", 0) / ratios.get("priceEarningsRatio", 1) if ratios.get("priceEarningsRatio", 0) > 0 else 0
                if eps_ttm > 0:
                    detailed_data["financial_metrics"]["eps"] = eps_ttm
                    
            if not detailed_data["financial_metrics"]["dividend_yield"] or detailed_data["financial_metrics"]["dividend_yield"] == 0:
                detailed_data["financial_metrics"]["dividend_yield"] = ratios.get("dividendYield", 0) * 100 or 0
                
            if not detailed_data["financial_metrics"]["profit_margin"] or detailed_data["financial_metrics"]["profit_margin"] == 0:
                detailed_data["financial_metrics"]["profit_margin"] = ratios.get("netProfitMargin", 0) or 0
            
        recommendations_url = f"https://financialmodelingprep.com/api/v3/rating/{symbol}?apikey={api_key}"
        recommendations_response = requests.get(recommendations_url)
        recommendations_data = recommendations_response.json()
        
        if recommendations_data and isinstance(recommendations_data, list) and len(recommendations_data) > 0:
            recommendation = recommendations_data[0].get('ratingRecommendation', 'NONE')
            detailed_data["financial_metrics"]["recommendation"] = recommendation
                        
        price_target_url = f"https://financialmodelingprep.com/api/v4/price-target?symbol={symbol}&apikey={api_key}"
        price_target_response = requests.get(price_target_url)
        price_target_data = price_target_response.json()
        
        if price_target_data and isinstance(price_target_data, list) and len(price_target_data) > 0:
            detailed_data["financial_metrics"]["target_price"] = price_target_data[0].get("priceTarget", 0)
        
        try:
            intraday_url = f"https://financialmodelingprep.com/api/v3/historical-chart/5min/{symbol}?apikey={api_key}"
            intraday_response = requests.get(intraday_url)
            intraday_data = intraday_response.json()
            
            if isinstance(intraday_data, list):
                intraday_data = sorted(intraday_data, key=lambda x: x.get("date", ""))
                
                recent_day_data = intraday_data[-78:] if len(intraday_data) > 78 else intraday_data
                
                daily_points = []
                for item in recent_day_data:
                    date_str = item.get("date", "")
                    close_price = item.get("close", 0)
                    
                    daily_points.append({
                        "date": date_str,
                        "close": float(close_price)
                    })
                
                detailed_data["historical_data"]["1d"]["data"] = daily_points
                detailed_data["historical_data"]["1d"]["interval"] = "5min"
        except Exception as e:
            print(f"Error fetching intraday data for {symbol}: {str(e)}")
        
        try:
            monthly_url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?timeseries=30&apikey={api_key}"
            monthly_response = requests.get(monthly_url)
            monthly_data = monthly_response.json()
            
            if "historical" in monthly_data and isinstance(monthly_data["historical"], list):
                monthly_points = []
                for item in monthly_data["historical"]:
                    date_str = item.get("date", "")
                    close_price = item.get("close", 0)
                    
                    monthly_points.append({
                        "date": date_str,
                        "close": float(close_price)
                    })
                
                monthly_points = sorted(monthly_points, key=lambda x: x.get("date", ""))
                detailed_data["historical_data"]["1mo"]["data"] = monthly_points
        except Exception as e:
            print(f"Error fetching monthly data for {symbol}: {str(e)}")
        
        try:
            yearly_url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?from={(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')}&to={datetime.now().strftime('%Y-%m-%d')}&apikey={api_key}"
            yearly_response = requests.get(yearly_url)
            yearly_data = yearly_response.json()
            
            if "historical" in yearly_data and isinstance(yearly_data["historical"], list):
                weekly_points = []
                by_week = {}
                
                for item in yearly_data["historical"]:
                    date_str = item.get("date", "")
                    try:
                        dt = datetime.strptime(date_str, "%Y-%m-%d")
                        year_week = f"{dt.year}-{dt.isocalendar()[1]}"
                        
                        if year_week not in by_week or dt > datetime.strptime(by_week[year_week].get("date"), "%Y-%m-%d"):
                            by_week[year_week] = item
                    except Exception as e:
                        print(f"Error processing date {date_str} for weekly data: {str(e)}")
                
                for item in by_week.values():
                    date_str = item.get("date", "")
                    close_price = item.get("close", 0)
                    
                    weekly_points.append({
                        "date": date_str,
                        "close": float(close_price)
                    })
                
                weekly_points = sorted(weekly_points, key=lambda x: x.get("date", ""))
                detailed_data["historical_data"]["1y"]["data"] = weekly_points
        except Exception as e:
            print(f"Error fetching yearly data for {symbol}: {str(e)}")
        
        try:
            five_year_url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?from={(datetime.now() - timedelta(days=365*5)).strftime('%Y-%m-%d')}&to={datetime.now().strftime('%Y-%m-%d')}&apikey={api_key}"
            five_year_response = requests.get(five_year_url)
            five_year_data = five_year_response.json()
            
            if "historical" in five_year_data and isinstance(five_year_data["historical"], list):
                monthly_points = []
                by_month = {}
                
                for item in five_year_data["historical"]:
                    date_str = item.get("date", "")
                    try:
                        dt = datetime.strptime(date_str, "%Y-%m-%d")
                        year_month = f"{dt.year}-{dt.month}"
                        
                        if year_month not in by_month or dt > datetime.strptime(by_month[year_month].get("date"), "%Y-%m-%d"):
                            by_month[year_month] = item
                    except Exception as e:
                        print(f"Error processing date {date_str} for monthly data: {str(e)}")
                
                for item in by_month.values():
                    date_str = item.get("date", "")
                    close_price = item.get("close", 0)
                    
                    monthly_points.append({
                        "date": date_str,
                        "close": float(close_price)
                    })
                
                monthly_points = sorted(monthly_points, key=lambda x: x.get("date", ""))
                detailed_data["historical_data"]["5y"]["data"] = monthly_points
        except Exception as e:
            print(f"Error fetching 5-year data for {symbol}: {str(e)}")
        
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