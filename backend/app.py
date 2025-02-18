from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

app = Flask(__name__, static_folder='frontend/dist', static_url_path='/')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@db:5432/spotify_sync')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

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