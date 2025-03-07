from flask import Blueprint, jsonify, request, redirect, session, url_for
from services import get_popular_stocks, get_stocks
import os
import jwt
from db import db
from models import User
from dotenv import load_dotenv
import extensions

load_dotenv()

api = Blueprint('api', __name__)

SECRET_KEY = os.environ.get("SECRET_KEY")
FRONTEND_URL = os.environ.get("FRONTEND_URL")

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

@api.route('/google/login')
def google_login():
    redirect_uri = os.getenv("REDIRECT_URI")
    return extensions.google.authorize_redirect(redirect_uri)

@api.route('/google/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200

@api.route('/google/callback')
def google_callback():
    try:
        token = extensions.google.authorize_access_token()
    except Exception as e:
        print("Error during token exchange:", e)
        return jsonify({"error": str(e)}), 400

    user_info = extensions.google.get("https://www.googleapis.com/oauth2/v2/userinfo").json()

    if not user_info:
        return jsonify({"error": "Failed to retrieve user information"}), 400

    existing_user = User.query.filter_by(email=user_info["email"]).first()

    if not existing_user:
        new_user = User(
            google_id=user_info["id"],
            name=user_info["name"],
            email=user_info["email"],
            profile_picture=user_info["picture"]
        )
        db.session.add(new_user)
    
    db.session.commit()

    user_token = jwt.encode(
        {"email": user_info["email"]}, SECRET_KEY, algorithm="HS256"
    )

    return redirect(f"{FRONTEND_URL}/?token={user_token}")
