import time
import datetime
from dateutil.tz import tzutc
import boto3
from . import awsKey, instances, VPCID, SubnetID, SecurityGroupID
ami = "ami-080ff70d8f5b80ba5"

def getAggregateMissRate1mins(instances: list, intervals=60, period=60):
    client = boto3.client('cloudwatch', 
                            region_name='us-east-1',
                            aws_access_key_id=awsKey.aws_access_key_id,
                            aws_secret_access_key=awsKey.aws_secret_access_key)
    startTime = datetime.datetime.utcnow() - datetime.timedelta(seconds=intervals)
    endTime = datetime.datetime.utcnow()
    miss = 0
    total= 0
    for i in instances:
        
        miss+=client.get_metric_statistics(
                Namespace='ece1779/memcache',
                MetricName='miss',
                Dimensions=[{
                        "Name": "instance",
                        "Value": i
                    }],
                StartTime = startTime,
                EndTime = endTime,
                Period=period,
                Statistics=['Sum'],
                Unit='Count',
                )['Datapoints']['Sum']
        
        total+=client.get_metric_statistics(
                Namespace='ece1779/memcache',
                MetricName='total',
                Dimensions=[{
                        "Name": "instance",
                        "Value": i
                    }],
                StartTime = startTime,
                EndTime = endTime,
                Period=period,
                Statistics=['Sum'],
                Unit='Count',
                )['Datapoints']['Sum']
            
    return miss/total
    
    
def getAggregateStat30Mins(instances: list):
    numberItems=[]
    currentSize=[]
    totalRequests=[]
    missRate=[]
    hitRate=[]
    client = boto3.client('cloudwatch', 
                        region_name='us-east-1',
                        aws_access_key_id=awsKey.aws_access_key_id,
                        aws_secret_access_key=awsKey.aws_secret_access_key)
    now=datetime.datetime.utcnow()
    for i in range (30,1,-1):
        startTime = now - datetime.timedelta(minutes=i)
        endTime = now - datetime.timedelta(minutes=i-1)
        miss = 0
        total= 0
        for i in instances:
            
            miss+=client.get_metric_statistics(
                    Namespace='ece1779/memcache',
                    MetricName='miss',
                    Dimensions=[{
                            "Name": "instance",
                            "Value": i
                        }],
                    StartTime = startTime,
                    EndTime = endTime,
                    Period=60,
                    Statistics=['Sum'],
                    Unit='Count',
                    )['Datapoints']['Sum']
            
            total+=client.get_metric_statistics(
                    Namespace='ece1779/memcache',
                    MetricName='total',
                    Dimensions=[{
                            "Name": "instance",
                            "Value": i
                        }],
                    StartTime = startTime,
                    EndTime = endTime,
                    Period=60,
                    Statistics=['Sum'],
                    Unit='Count',
                    )['Datapoints']['Sum']
            
            numItem=client.get_metric_statistics(
                    Namespace='ece1779/memcache',
                    MetricName='numberItems',
                    Dimensions=[{
                            "Name": "instance",
                            "Value": i
                        }],
                    StartTime = startTime,
                    EndTime = endTime,
                    Period=60,
                    Statistics=['Average'],
                    Unit='Count',
                    )['Datapoints']['Average']
            
            size=client.get_metric_statistics(
                    Namespace='ece1779/memcache',
                    MetricName='currentSize',
                    Dimensions=[{
                            "Name": "instance",
                            "Value": i
                        }],
                    StartTime = startTime,
                    EndTime = endTime,
                    Period=60,
                    Statistics=['Average'],
                    Unit='Count',
                    )['Datapoints']['Average']
                
        missRate.append(miss/total)
        hitRate.append(1-miss/total)
        totalRequests.append(total)
        numberItems.append(numItem)
        currentSize.append(size)
    return [numberItems,
    currentSize,
    totalRequests,
    missRate,
    hitRate]
          

        

    
    
    
    
    

        