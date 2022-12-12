"""
 * __init__.py
 * Front-end instance constructor
 *
 * Author: Weixuan Yang
 * Date: Dec 12, 2022
"""
import boto3
from flask import Flask
from . import config
front = Flask(__name__)
s3 = boto3.client('s3',
                  region_name=config.aws_key['aws_region'],
                  aws_access_key_id=config.aws_key['aws_access_key_id'],
                  aws_secret_access_key=config.aws_key['aws_secret_access_key'])
from . import frontend
