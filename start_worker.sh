#!/bin/bash
cd backend
exec celery -A tasks.celery_app worker --loglevel=info --concurrency=4
