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
if 'Games' not in s3_client.list_buckets()['Buckets']['Name']:
    rank_bucket = s3.create_bucket(Bucket='Games')
rank_bucket = s3.Bucket(name='Games')


dynamodb_client = boto3.client('dynamodb',
                               region_name=config.aws_key['aws_region'],
                               aws_access_key_id=config.aws_key['aws_access_key_id'],
                               aws_secret_access_key=config.aws_key['aws_secret_access_key'])
dynamodb = boto3.resource('dynamodb',
                          region_name=config.aws_key['aws_region'],
                          aws_access_key_id=config.aws_key['aws_access_key_id'],
                          aws_secret_access_key=config.aws_key['aws_secret_access_key'])
if 'Games' not in dynamodb_client.list_tables()['TableNames']:
    games_table = dynamodb.create_table(TableName="Games",
                                        KeySchema=[
                                            {'AttributeName': 'GameId', 'KeyType': 'HASH'}
                                        ],
                                        AttributeDefinitions=[
                                            {'AttributeName': 'GameId', 'AttributeType': 'S'},
                                            {'AttributeName': 'FoeId', 'AttributeType': 'S'},
                                            {'AttributeName': 'HostId', 'AttributeType': 'S'},
                                            {'AttributeName': 'Statusnow', 'AttributeType': 'S'}
                                        ],
                                        ProvisionedThroughput={
                                            'ReadCapacityUnits': 1,
                                            'WriteCapacityUnits': 1
                                        },
                                        GlobalSecondaryIndexes=[
                                            {
                                                'IndexName': 'FoeId',
                                                'KeySchema': [
                                                    {
                                                        'AttributeName': 'FoeId',
                                                        'KeyType': 'HASH',

                                                    },

                                                    {
                                                        'AttributeName': 'Statusnow',
                                                        'KeyType': 'RANGE',
                                                    }

                                                ],
                                                'Projection': {
                                                    'ProjectionType': 'ALL',

                                                },
                                                'ProvisionedThroughput': {
                                                    'ReadCapacityUnits': 1,
                                                    'WriteCapacityUnits': 1
                                                }
                                            },
                                            {
                                                'IndexName': 'HostId',
                                                'KeySchema': [
                                                    {
                                                        'AttributeName': 'HostId',
                                                        'KeyType': 'HASH',

                                                    },

                                                    {
                                                        'AttributeName': 'Statusnow',
                                                        'KeyType': 'RANGE',
                                                    }
                                                ],
                                                'Projection': {
                                                    'ProjectionType': 'ALL',

                                                },
                                                'ProvisionedThroughput': {
                                                    'ReadCapacityUnits': 1,
                                                    'WriteCapacityUnits': 1
                                                }
                                            }
                                        ]
                                        )
    games_table.wait_until_exists()
game_table = dynamodb.Table('Games')
from . import frontend
