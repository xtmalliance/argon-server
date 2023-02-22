web: gunicorn flight_blender:app
worker: celery worker --app=flight_blender
beat: celery --app=flight_blender beat -loglevel info 