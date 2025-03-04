from flask import Flask, jsonify
from flask_cors import CORS
import os
from flask_migrate import Migrate
from routes import api
from db import db, init_db
from sqlalchemy import text

app = Flask(__name__)

origins_str = os.environ.get("ALLOWED_ORIGINS")

if origins_str:
    origins = origins_str.split(",")
    CORS(app, origins=origins)
else:
    raise ValueError("ALLOWED_ORIGINS environment variable must be set in production")


DATABASE_URL = os.getenv("DATABASE_URL")

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

init_db(app)
migrate = Migrate(app, db)

app.register_blueprint(api, url_prefix="/api")

@app.route('/')
def hello():
    return "hello"


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
