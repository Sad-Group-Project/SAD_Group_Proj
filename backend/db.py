from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    """Initialize the database with the Flask app."""
    db.init_app(app)

    with app.app_context():
        from models import User
        db.create_all()
