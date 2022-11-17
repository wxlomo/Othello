import os
os.system('gunicorn --bind 0.0.0.0:5001 --workers 1 run:mem')