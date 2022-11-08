#!../venv/bin/python
from app import front
if __name__ == '__main__':
    front.run('0.0.0.0', 5000, debug=True, threaded=True)


