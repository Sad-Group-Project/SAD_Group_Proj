from flask import Blueprint, jsonify, request, redirect, session, url_for
from services import get_popular_stocks, get_stocks, get_add_stock, get_users_stocks, get_user_profile
from config import get_google_provider_cfg, client, GOOGLE_CLIENT_SECRET, GOOGLE_CLIENT_ID
import os
import json
from functools import wraps
import jwt
import requests
import datetime
from db import db
from models import User
from flask_login import (
    login_user,
    login_required,
    logout_user,
)


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

@api.route('/save_stock', methods=['OPTIONS', 'POST'])
def save_stock():
    if request.method == "OPTIONS":
        response = jsonify({"message": "CORS preflight OK"})
        origin = request.headers.get("Origin")
        response.headers.add("Access-Control-Allow-Origin", origin)
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Authorization, Content-Type")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response, 200

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400
    stock_symbol = data.get('symbol')
    return get_add_stock(stock_symbol, SECRET_KEY)

@api.route('/user_stocks')
def user_stocks():
    return get_users_stocks(SECRET_KEY)

@api.route('/user_profile')
def user_profile():
    return get_user_profile(SECRET_KEY)

@api.route('google/login', methods=['GET', 'POST'])
def login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=os.environ.get("REDIRECT_URI"),
        scope=["openid", "email", "profile"]
    )
    return redirect(request_uri)

@api.route('google/callback')
def callback():
    code = request.args.get("code")

    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)
    )

    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "USER EMAIL NOT AVAILABLE", 400
    
    session["google_id"] = unique_id
    session.permanent = True  
    
    user = User.query.filter_by(google_id=unique_id).first()

    if not user:
        user = User(google_id=unique_id, name=users_name, email=users_email, profile_picture=picture)
        db.session.add(user)
        db.session.commit()

    login_user(user)

    token_payload = {
        "user_id": user.id,
        "google_id": user.google_id,
        "email": user.email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    token = jwt.encode(token_payload, SECRET_KEY, algorithm="HS256")

    frontend_url = os.getenv("FRONTEND_URL")
    return redirect(f"{frontend_url}/?token={token}")


@api.route("google/logout", methods=["POST"])
def logout():
    if "user_id" in session:
        logout_user()
        session.clear()
        return jsonify({"message": "Logged out successfully"}), 200
    else:
        return jsonify({"message": "User was not logged in"}), 200 


def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Token is missing!"}), 401
        
        try:
            token = token.split("Bearer ")[1]
            secret_key = os.getenv("SECRET_KEY")
            decoded_token = jwt.decode(token, secret_key, algorithms=["HS256"])
            return f(decoded_token, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token!"}), 401

    return decorated_function

@api.route('/auth/verify', methods=['GET'])
@token_required
def verify_token(decoded_token):
    return jsonify({"authenticated": True, "user": decoded_token}), 200

