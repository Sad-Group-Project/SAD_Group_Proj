from flask import Flask, redirect, request, url_for
from flask_cors import CORS
import os
from flask_migrate import Migrate
from db import db, init_db
from oauthlib.oauth2 import WebApplicationClient
from flask_login import LoginManager
from models import User
import requests


app = Flask(__name__)
app.secret_key=os.environ.get("SECRET_KEY")

if os.environ.get("FLASK_ENV") == "development":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

origins_str = os.environ.get("ALLOWED_ORIGINS")
if origins_str:
    origins = origins_str.split(",")
    CORS(app, origins=origins, supports_credentials=True)
else:
    raise ValueError("ALLOWED_ORIGINS environment variable must be set in production")

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

login_manager=LoginManager()
login_manager.init_app(app)

GOOGLE_CLIENT_ID=os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET=os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL="https://accounts.google.com/.well-known/openid-configuration"

client=WebApplicationClient(GOOGLE_CLIENT_ID)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

init_db(app)

migrate = Migrate(app, db)

from routes import api


app.register_blueprint(api, url_prefix="/api")

@app.route('/')
def hello():
    return "Hello, world!"

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8080, ssl_context=None)
