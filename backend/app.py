from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime




app = Flask(__name__, static_folder='frontend/dist', static_url_path='/')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 'postgresql://user:password@localhost:5432/spotify_sync')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
class User(db.Model):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    spotify_id = Column(String, unique=True, nullable=False)  # Spotify User ID
    access_token = Column(String, nullable=False)  # OAuth Access Token
    refresh_token = Column(String, nullable=False)  # OAuth Refresh Token
    token_expires_at = Column(DateTime, nullable=False)  # Token Expiry
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    # Last sync time (nullable)
    last_synced_at = Column(DateTime, default=None)


@app.route('/api/hello')
def hello():
    return {'message': 'Hello from Flask API!'}

# Serve React frontend


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
