#!../venv/bin/python
from app import scaler
if __name__ == '__main__':
    scaler.run('0.0.0.0', port=5003, debug=False, threaded=True)


