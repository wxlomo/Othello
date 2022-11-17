# import os
# os.system('gunicorn --bind 0.0.0.0:5001 --chdir ~/ECE1779-Group9-Project-Code/A_2/memcache --workers 1 run:mem')
from app import mem
if __name__ == '__main__':
    mem.run('0.0.0.0', port=5001, debug=False, threaded=True)
