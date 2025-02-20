#!/bin/sh

# Exit on error
set -e

# Run migrations
flask db upgrade

# Start the Flask app
exec python app.py
