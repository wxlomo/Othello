#!../venv/bin/python
from app import mem
if __name__ == '__main__':
    mem.run('0.0.0.0', port=5001, debug=False, threaded=True)


