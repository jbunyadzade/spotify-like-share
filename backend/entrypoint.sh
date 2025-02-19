#!/bin/sh

# Exit on error
set -e

# Wait for the database to be ready (optional)
# You can add a loop here to check for DB readiness

# Run migrations
flask db upgrade

# Start the Flask app
exec python app.py
