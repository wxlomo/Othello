#!../venv/bin/python
import boto3
from app import front


if __name__ == '__main__':
    front.run('0.0.0.0', 5000, debug=False, threaded=True)


