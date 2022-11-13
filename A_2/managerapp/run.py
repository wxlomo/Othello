#!../venv/bin/python
from app import manager
if __name__ == '__main__':
    manager.run('0.0.0.0', 5002, debug=True, threaded=True)


