from flask import Blueprint, jsonify, request, redirect, session, url_for
from services import get_popular_stocks, get_stocks, get_save_stock
import os
from functools import wraps
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

@api.route('/save_stock', methods=['OPTIONS', 'POST'])
def save_stock():
    if request.method == "OPTIONS":
        response = jsonify({"message": "CORS preflight OK"})
        origin = request.headers.get("Origin")
        response.headers.add("Access-Control-Allow-Origin", origin)
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response, 200

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400
    stock_symbol = data.get('symbol')
    return get_save_stock(stock_symbol)

@api.route('/google/login')
def google_login():
    redirect_uri = os.getenv("REDIRECT_URI")
    response = extensions.google.authorize_redirect(redirect_uri)
    return response

@api.route('/google/logout', methods=['POST'])
def logout():
    session.pop("google_id", None)
    session.modified = True
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
        user_id = new_user.id
    else:
        user_id = existing_user.id

    session['google_id'] = user_info["id"]
    session.modified = True

    user_token = jwt.encode(
        {"user_id": user_id, "email": user_info["email"]}, SECRET_KEY, algorithm="HS256"
    )

    return redirect(f"{FRONTEND_URL}/?token={user_token}")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"message": "Token is missing!"}), 401

        try:
            token = token.split(" ")[1]
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            
            print("Decoded Token:", decoded)
            
            if "user_id" not in decoded:
                return jsonify({"message": "Invalid token: 'user_id' missing"}), 401

            return f(decoded["user_id"], *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token!"}), 401

    return decorated

@api.route("/auth/verify", methods=["GET"])
@token_required 
def verify_token(user_id):
    return jsonify({"message": "Token is valid", "user_id": user_id}), 200
