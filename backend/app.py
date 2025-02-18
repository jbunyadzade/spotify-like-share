from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import jwt
import datetime
from flask import Flask, redirect, request, session, jsonify, url_for, make_response, send_from_directory
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, static_folder='frontend/dist', static_url_path='/')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@db:5432/spotify_sync')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

SPOTIPY_CLIENT_ID = os.getenv("CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:5000/callback'
SCOPE = 'user-library-read playlist-modify-public playlist-read-private'

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_SECONDS = 3600

# Set up Spotipy's OAuth object
sp_oauth = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope=SCOPE
)


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


@app.route('/api/login', methods=['POST'])
def login():
    # Redirect user to Spotify's OAuth page
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route('/api/callback', methods=['POST'])
def callback():
    # Retrieve authorization code from callback URL
    code = request.args.get('code')
    if not code:
        return "Error: Missing code parameter", 400

    # Get token info from Spotify
    token_info = sp_oauth.get_access_token(code)
    if not token_info:
        return "Error: Could not retrieve token", 400

    # Save token info in session (for demonstration; in production use a database)
    session['token_info'] = token_info

    # Get the user's profile using Spotipy
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_profile = sp.current_user()
    user_email = user_profile.get('email')
    user_id = user_profile.get('id')

    # Create a JWT token containing user's email and Spotify id
    payload = {
        'email': user_email,
        'spotify_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXP_DELTA_SECONDS)
    }
    jwt_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # Create a response that sets the JWT as an HTTP-only cookie and redirect to /home.
    response = make_response(redirect(url_for('home')))
    response.set_cookie('jwt', jwt_token, httponly=True, samesite='Lax', expires=3600)
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)