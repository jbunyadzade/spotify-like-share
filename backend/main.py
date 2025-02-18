import os
import jwt
import datetime
from flask import Flask, redirect, request, session, jsonify, url_for, make_response, render_template_string
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("API_SECRET")


# Spotify API configuration
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

@app.route('/')
def index():
    # If the user has the JWT cookie, redirect to home; otherwise, show a login link.
    jwt_token = request.cookies.get('jwt')
    if jwt_token:
        return redirect(url_for('home'))
    return '<h2>Welcome</h2><a href="/login">Login with Spotify</a>'


@app.route('/login')
def login():
    # Redirect user to Spotify's OAuth page
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route('/callback')
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
    response.set_cookie('jwt', jwt_token, httponly=True, samesite='Lax')
    return response


@app.route('/home')
def home():
    # Home page that displays a sync button
    html_content = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Home</title>
      </head>
      <body>
        <h1>Welcome to Your Spotify Sync Dashboard</h1>
        <form action="/sync" method="post">
          <button type="submit">Sync Liked Songs</button>
        </form>
      </body>
    </html>
    """
    return render_template_string(html_content)


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


@app.route('/sync', methods=['POST'])
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

        liked_tracks.update(item['track']['id'] for item in items if item.get('track'))
        offset += limit


    # Check if a playlist named "Public Likes" exists; if not, create it.
    playlists = sp.current_user_playlists(limit=50)
    public_playlist = None
    for playlist in playlists.get('items', []):
        if playlist.get('name') == 'Public Likes':
            public_playlist = playlist
            break

    if not public_playlist:
        public_playlist = sp.user_playlist_create(user=user_id, name='Public Likes', public=True)

    playlist_id = public_playlist['id']


    playlist_tracks = set()
    offset = 0
    limit = 100  # Max per request

    while True:
        results = sp.playlist_tracks(playlist_id, limit=limit, offset=offset)
        items = results.get('items', [])

        if not items:
            break

        playlist_tracks.update(item['track']['id'] for item in items if item.get('track'))
        offset += limit


    # Determine tracks to add and remove
    to_add = liked_tracks - playlist_tracks
    to_remove = playlist_tracks - liked_tracks

    # Update playlist
    if to_add:
        sp.playlist_add_items(playlist_id, list(to_add))
        print(f"Added {len(to_add)} tracks.")

    if to_remove:
        sp.playlist_remove_all_occurrences_of_items(playlist_id, list(to_remove))
        print(f"Removed {len(to_remove)} tracks.")

    if not to_add and not to_remove:
        print("Playlist is already up to date.")

    return jsonify({'message': 'Liked songs have been synced to "Public Likes".', 'playlist_id': playlist_id})


if __name__ == '__main__':
    app.run(debug=True)