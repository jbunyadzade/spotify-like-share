# Spotify Liked Songs Sync Tool

## Overview
Spotify does not allow users to make their 'Liked Songs' public. This tool automatically syncs 'Liked Songs' to a public playlist, making it easier to share music with friends.

## Features
- **Automatic Syncing**: Keeps a public playlist updated with your 'Liked Songs'.
- **Authentication**: Uses Spotify login only, no extra user data stored.
- **Syncing Behavior**:
  - Free users: Weekly syncs.
  - Paid users: Custom sync frequency + manual syncs.
- **Playlist Management**:
  - Default playlist name: "Liked Songs Sync".
  - Paid users can rename, filter, and control playlist visibility.
- **Notifications**: Get notified when a sync occurs.

## Monetization
- **Free Tier**: Ads + weekly syncs.
- **Paid Tier**: Subscription-based with custom syncs, filtering, renaming, and unlimited manual syncs.

## Future Considerations
- Multi-playlist support.
- Analytics dashboard.
- More integrations.

## Installation & Setup
### Prerequisites
- Python (with `venv` support)
- Node.js
- Spotify Developer Account

### Steps
1. Clone the repository:
   ```sh
   git clone https://github.com/jbunyadzade/spotify-like-share.git
   cd spotify-liked-songs-sync
   ```
2. Set up the backend:
   ```sh
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```
3. Run the backend:
   ```sh
   python app.py
   ```
4. Set up the frontend:
   ```sh
   cd frontend
   npm install
   npm start
   ```


## Contributing
Feel free to submit pull requests or open issues to suggest improvements!

## License
MIT License

