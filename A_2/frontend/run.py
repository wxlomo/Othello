#!../venv/bin/python
import boto3
from app import front, config


s3 = boto3.client('s3')
s3.create_bucket(Bucket=config.s3_config['name'],
                 CreateBucketConfiguration={'LocationConstraint': config.s3_config['region_name']})
if __name__ == '__main__':
    front.run('0.0.0.0', 5000, debug=False, threaded=True)


