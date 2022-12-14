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
from uuid import uuid4

front = Flask(__name__)
front.secret_key = str(uuid4())
s3_client = boto3.client('s3',
                         region_name=config.aws_key['aws_region'],
                         aws_access_key_id=config.aws_key['aws_access_key_id'],
                         aws_secret_access_key=config.aws_key['aws_secret_access_key'])
s3 = boto3.resource('s3',
                    region_name=config.aws_key['aws_region'],
                    aws_access_key_id=config.aws_key['aws_access_key_id'],
                    aws_secret_access_key=config.aws_key['aws_secret_access_key'])
dynamodb_client = boto3.client('dynamodb',
                               region_name=config.aws_key['aws_region'],
                               aws_access_key_id=config.aws_key['aws_access_key_id'],
                               aws_secret_access_key=config.aws_key['aws_secret_access_key'])
db = boto3.resource('dynamodb',
                    region_name=config.aws_key['aws_region'],
                    aws_access_key_id=config.aws_key['aws_access_key_id'],
                    aws_secret_access_key=config.aws_key['aws_secret_access_key'])
from . import frontend
