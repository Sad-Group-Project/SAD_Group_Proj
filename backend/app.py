from flask import Flask
from flask_cors import CORS
import os

app = Flask(__name__)

FRONTEND_URL = os.getenv("FRONTEND_URL")
PRODUCTION_FRONTEND_URL = os.getenv("PRODUCTION_FRONTEND_URL")

print("FRONTEND_URL:", os.getenv("FRONTEND_URL"))
print("PRODUCTION_FRONTEND_URL:", os.getenv("PRODUCTION_FRONTEND_URL"))

origins = [url for url in [FRONTEND_URL, PRODUCTION_FRONTEND_URL] if url]

print("Allowed CORS Origins:", origins)

CORS(app, resources={r"/*": {"origins": origins}})

@app.route('/')
def hello():
    return "Hello, Backend connected!"

@app.route('/api/stocks')
def home():
    return "Hello, Flask!"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
