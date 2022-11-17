import os
os.system('cd ~/ECE1779-Group9-Project-Code/A_2/memcache/runmemcache.py && gunicorn --bind 0.0.0.0:5001 --workers 1 run:mem')