from flask import Blueprint, jsonify, request
from services import get_popular_stocks, get_stocks

api = Blueprint('api', __name__)

@api.route('/popular_stocks', methods=['GET'])
def popular_stocks():
    return get_popular_stocks()

@api.route('/stocks', methods=['GET'])
def stocks():
    stock_symbol = request.args.get('symbol')
    return get_stocks(stock_symbol)

@api.route('/debug')
def debug():
    return jsonify({
        'url': request.url,
        'scheme': request.scheme,
        'headers': dict(request.headers)
    })