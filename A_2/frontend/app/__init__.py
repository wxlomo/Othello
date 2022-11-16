"""
 * __init__.py
 * Front-end instance constructor
 *
 * Author: Weixuan Yang
 * Date: Oct. 11, 2022
"""
import boto3
from flask import Flask
from . import config
#from config import awsKey
awsKey = config.awsKey
front = Flask(__name__)
s3 = boto3.client('s3', 
                        region_name='us-east-1',
                        aws_access_key_id=awsKey['aws_access_key_id'],
                        aws_secret_access_key=awsKey['aws_secret_access_key'])
rds = boto3.client('rds', 
                        region_name='us-east-1',
                        aws_access_key_id=awsKey['aws_access_key_id'],
                        aws_secret_access_key=awsKey['aws_secret_access_key'])

from . import frontend
