import os
import requests
from oauthlib.oauth2 import WebApplicationClient


ENV = os.environ.get("FLASK_ENV")

SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

SQLALCHEMY_TRACK_MODIFICATIONS = False

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

client = WebApplicationClient(GOOGLE_CLIENT_ID)

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()
