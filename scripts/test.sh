#!/usr/bin/env bash

# Uncomment below if you have a different test file for tests
# export $(grep -v '^#' .env.test | xargs)

# Start redis server and run it in the background
echo "Starting redis server in the background..."
redis-server --daemonize yes

# Clear redis incase prod/live data and secrets and still
# saved in cache
echo "Clearing all redis data..."
redis-cli FLUSHDB

echo "Running tests $1"
python manage.py test $1
