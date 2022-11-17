import os
os.system('gunicorn --bind 0.0.0.0:5001 --chdir ~/ECE1779-Group9-Project-Code/A_2/memcache --workers 1 run:mem')