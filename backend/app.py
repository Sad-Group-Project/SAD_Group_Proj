from flask import Flask, jsonify
from flask_cors import CORS
import os
from flask_migrate import Migrate
from routes import api
from db import db, init_db
from extensions import oauth
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

origins_str = os.environ.get("ALLOWED_ORIGINS")
if origins_str:
    origins = origins_str.split(",")
    CORS(app, origins=origins, supports_credentials=True)
else:
    raise ValueError("ALLOWED_ORIGINS environment variable must be set in production")

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

oauth.init_app(app)

google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    access_token_url="https://oauth2.googleapis.com/token",
    api_base_url="https://www.googleapis.com/oauth2/v2/",
    client_kwargs={"scope": "openid email profile"},
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
)

import extensions
extensions.google = google

DATABASE_URL = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

init_db(app)
migrate = Migrate(app, db)

app.register_blueprint(api, url_prefix="/api")

@app.route('/')
def hello():
    return "Hello, world!"

@app.route('/debug_db')
def debug_db():
    try:
        with db.engine.connect() as connection:
            result = connection.execute(text("SELECT 'Database Connection Successful'")).fetchone()
            return jsonify({"message": result[0]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080, ssl_context=None)
