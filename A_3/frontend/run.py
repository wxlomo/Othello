#!../venv/bin/python
import boto3
from app import front


if __name__ == '__main__':
    front.run(debug=True)


