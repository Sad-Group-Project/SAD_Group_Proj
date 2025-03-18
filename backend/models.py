from db import db
from datetime import datetime

class User(db.Model):
    __tablename__='users'
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    profile_picture = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class SavedStocks(db.Model):
    __tablename__='saved_stocks'
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(255), db.ForeignKey('users.google_id', ondelete="CASCADE"), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    company_name = db.Column(db.String(255))
    price_at_save = db.Column(db.Float)
    date_save = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('saved_stocks', lazy=True))