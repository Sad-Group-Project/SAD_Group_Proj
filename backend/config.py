import os
from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv("FLASK_ENV")

SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URI:
    raise ValueError("DATABASE_URL is not set. Check your environment variables.")

SQLALCHEMY_TRACK_MODIFICATIONS = False
