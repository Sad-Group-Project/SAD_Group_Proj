from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

app.config["FRONTEND_URL"] = os.getenv("FRONTEND_URL")
API_BASE_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5173")
PRODUCTION_FRONTEND_URL = os.getenv("PRODUCTION_FRONTEND_URL")



CORS(app, origins=[API_BASE_URL, PRODUCTION_FRONTEND_URL])

@app.route('/')
def hello():
    return "Hello, Backend connected"

@app.route('/api/stocks')
def home():
    return "Hello, Flask!"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
