from flask import Flask, redirect, request, url_for
from flask_cors import CORS
import os
from flask_migrate import Migrate
from db import db, init_db
from oauthlib.oauth2 import WebApplicationClient
from flask_login import LoginManager
from flask_session import Session
from models import User


app = Flask(__name__)
app.secret_key=os.environ.get("SECRET_KEY")

if os.environ.get("FLASK_ENV") == "development" or os.environ.get("FLASK_ENV") == "production":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

origins_str = os.environ.get("ALLOWED_ORIGINS")
if origins_str:
    origins = origins_str.split(",")
    CORS(app, origins=origins, supports_credentials=True)
else:
    raise ValueError("ALLOWED_ORIGINS environment variable must be set in production")

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_KEY_PREFIX"] = "flask_session:"

Session(app)

login_manager=LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

init_db(app)

migrate = Migrate(app, db)

from routes import api


app.register_blueprint(api, url_prefix="/api")

@app.route('/')
def hello():
    return "Hello, world!"

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8080, ssl_context=None)
