#!/usr/bin/env bash

# Uncomment command below if you are having
# ´ModuleNotFoundError: No module named 'app´ errors
# export PYTHONPATH=$PWD

# Start redis server and run it in the background
echo "Starting redis server in the background..."
redis-server --daemonize yes

# Check if background redis-server started successfully
# ps aux | grep redis-server

# To stop redis server running in background
# sudo /etc/init.d/redis-server stop

# Start Celery in a different terminal
# celery -A majibu.celery beat
# celery -A majibu worker --loglevel=info
