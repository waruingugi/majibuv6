#!/usr/bin/env bash

# Uncomment command below if you are having
# ´ModuleNotFoundError: No module named 'app´ errors
# export PYTHONPATH=$PWD

# Start redis server and run it in the background
# echo "Starting redis server in the background..."
# redis-server --daemonize yes

# Check if Redis is running
if pgrep -x "redis-server" > /dev/null
then
    echo "Redis is running..."
else
    echo "Redis is not running. Starting Redis..."
    redis-server --daemonize yes
    if [ $? -eq 0 ]; then
        echo "Redis started successfully"
    else
        echo "Failed to start Redis"
    fi
fi

# Start the server
python manage.py runserver

# Check if background redis-server started successfully
# ps aux | grep redis-server

# To stop redis server running in background
# sudo /etc/init.d/redis-server stop

# Start Celery in a different terminal
# celery -A majibu.celery beat
# celery -A majibu worker --loglevel=info
