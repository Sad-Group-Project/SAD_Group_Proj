from flask import Flask, redirect, request, url_for, abort
from flask_cors import CORS
import os
from flask_migrate import Migrate
from db import db, init_db
from oauthlib.oauth2 import WebApplicationClient
from flask_login import LoginManager
from flask_session import Session
from models import User

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

if os.environ.get("FLASK_ENV") == "development" or os.environ.get("FLASK_ENV") == "production":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

origins_str = os.environ.get("ALLOWED_ORIGINS")
if origins_str:
    origins = origins_str.split(",")
    CORS(app, origins=origins, supports_credentials=True, allow_headers=["Authorization", "Content-Type"])
else:
    raise ValueError("ALLOWED_ORIGINS environment variable must be set in production")

@app.before_request
def block_unapproved_origins():
    skip_paths = os.environ.get("SKIP_ORIGIN_CHECK_PATHS", "").split(",")
    if any(request.path.startswith(path) for path in skip_paths):
        return

    allowed_origins = os.environ.get("ALLOWED_ORIGINS", "").split(",")
    origin = request.headers.get("Origin")

    if not origin or origin not in allowed_origins:
        abort(403)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

login_manager = LoginManager()
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
