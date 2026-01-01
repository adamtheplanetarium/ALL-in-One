#!/bin/bash
set -e
cd "$(dirname "$0")/backend"
exec gunicorn --worker-class gevent -w 1 --bind 0.0.0.0:$PORT app:app
