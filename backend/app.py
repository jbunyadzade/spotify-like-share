from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import Column, Integer, String, DateTime
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
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 'postgresql://user:password@db:5432/spotify_sync')
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
    is_active: Mapped[bool] = mapped_column(default=False)


SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
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


@app.route('/api/login', methods=['POST'])
def login():
    # Redirect user to Spotify's OAuth page
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route('/api/add-spotify-user', methods=['POST'])
def add_spotify_user():
    data = request.get_json()
    spotify_id = data.get('spotify_id')
    access_token = data.get('access_token')
    refresh_token = data.get('refresh_token')
    token_expires_at = data.get('token_expires_at')
    is_active = data.get('is_active', True)

    if not all([spotify_id, access_token, refresh_token, token_expires_at]):
        return jsonify({'error': 'Missing required fields'}), 400

    user = User(
        spotify_id=spotify_id,
        access_token=access_token,
        refresh_token=refresh_token,
        token_expires_at=datetime.datetime.strptime(
            token_expires_at, '%Y-%m-%d'),
        is_active=is_active
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User added successfully!'})


@app.route('/api/get-spotify-user')
def get_spotify_user():
    spotify_id = request.args.get('spotify_id')
    if not spotify_id:
        return jsonify({'error': 'spotify_id query parameter is required'}), 400

    user = User.query.filter_by(spotify_id=spotify_id).first()
    if user:
        return jsonify({'message': 'User found', 'user': {
            'id': user.id,
            'spotify_id': user.spotify_id,
            'access_token': user.access_token,
            'refresh_token': user.refresh_token,
            'token_expires_at': user.token_expires_at,
            'created_at': user.created_at,
            'last_synced_at': user.last_synced_at,
            'is_active': user.is_active
        }})
    else:
        return jsonify({'message': 'User not found'}), 404


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
    response.set_cookie('jwt', jwt_token, httponly=True,
                        samesite='Lax', expires=3600)
    return response


def get_spotify_client(token_info):
    """Helper to create a Spotipy client given token info."""
    return spotipy.Spotify(auth=token_info['access_token'])


def fetch_user_token_info(user_id):
    """
    This function should retrieve the stored token info for a given user.
    For demonstration, we'll assume it's stored in the session.
    In production, you would use a database to store and refresh tokens.
    """
    token_info = session.get('token_info')
    if token_info and token_info.get('access_token'):
        return token_info
    return None


@app.route('/api/sync', methods=['POST'])
def sync():
    # Retrieve the JWT from cookies
    jwt_token = request.cookies.get('jwt')
    if not jwt_token:
        return jsonify({'error': 'JWT token not found in cookies'}), 401

    try:
        payload = jwt.decode(jwt_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_email = payload.get('email')
        user_id = payload.get('spotify_id')
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'JWT token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid JWT token'}), 401

    # Retrieve the user's token info (in production, retrieve from your database)
    token_info = fetch_user_token_info(user_id)
    if not token_info:
        return jsonify({'error': 'User token info not found'}), 404

    sp = get_spotify_client(token_info)

    # Getting Liked songs

    liked_tracks = set()
    offset = 0
    limit = 50  # Max per request

    while True:
        results = sp.current_user_saved_tracks(limit=limit, offset=offset)
        items = results.get('items', [])

        if not items:
            break  # Stop when no more tracks

        liked_tracks.update(item['track']['id']
                            for item in items if item.get('track'))
        offset += limit

    # Check if a playlist named "Public Likes" exists; if not, create it.
    playlists = sp.current_user_playlists(limit=50)
    public_playlist = None
    for playlist in playlists.get('items', []):
        if playlist.get('name') == 'Public Likes':
            public_playlist = playlist
            break

    if not public_playlist:
        public_playlist = sp.user_playlist_create(
            user=user_id, name='Public Likes', public=True)

    playlist_id = public_playlist['id']

    playlist_tracks = set()
    offset = 0
    limit = 100  # Max per request

    while True:
        results = sp.playlist_tracks(playlist_id, limit=limit, offset=offset)
        items = results.get('items', [])

        if not items:
            break

        playlist_tracks.update(item['track']['id']
                               for item in items if item.get('track'))
        offset += limit

    # Determine tracks to add and remove
    to_add = liked_tracks - playlist_tracks
    to_remove = playlist_tracks - liked_tracks

    # Update playlist
    if to_add:
        sp.playlist_add_items(playlist_id, list(to_add))
        print(f"Added {len(to_add)} tracks.")

    if to_remove:
        sp.playlist_remove_all_occurrences_of_items(
            playlist_id, list(to_remove))
        print(f"Removed {len(to_remove)} tracks.")

    if not to_add and not to_remove:
        print("Playlist is already up to date.")

    return jsonify({'message': 'Liked songs have been synced to "Public Likes".', 'playlist_id': playlist_id})

# Serve React frontend


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
