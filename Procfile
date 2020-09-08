web: gunicorn -b 0.0.0.0:$PORT app:app
worker: celery -A app.celery worker -loglevel info 
beat: celery -A app.celery beat -loglevel info 