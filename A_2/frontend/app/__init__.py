"""
 * __init__.py
 * Front-end instance constructor
 *
 * Author: Weixuan Yang
 * Date: Oct. 11, 2022
"""
import boto3
from flask import Flask

front = Flask(__name__)
s3 = boto3.client('s3')
rds = boto3.client('rds')

from . import frontend
