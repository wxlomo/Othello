import time
import datetime
from dateutil.tz import tzutc
import boto3
from . import cloudwatch_config, instances
ami = "ami-080ff70d8f5b80ba5"

def getAggregateMissRate1mins(instances: list, intervals=60, period=60):
    client = boto3.client('cloudwatch', 
                            region_name='us-east-1',
                            aws_access_key_id=cloudwatch_config.aws_access_key_id,
                            aws_secret_access_key=cloudwatch_config.aws_secret_access_key)
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
                        aws_access_key_id=cloudwatch_config.aws_access_key_id,
                        aws_secret_access_key=cloudwatch_config.aws_secret_access_key)
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
          
# def grep_vpc_subnet_id():
#     ec2_client = boto3.client('ec2',
#                             "us-east-1",
#                             aws_access_key_id=cloudwatch_config.aws_access_key_id,
#                             aws_secret_access_key=cloudwatch_config.aws_secret_access_key)
#     response = ec2_client.describe_vpcs()
#     vpc_id = ""
#     print(response)
#     for vpc in response["Vpcs"]:
#         if vpc["InstanceTenancy"].__contains__("default"):
#             vpc_id = vpc["VpcId"]
#             break
#     print("The Default VPC : ", vpc_id)
#     response = ec2_client.describe_subnets(
#         Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
#     subnet_id = response["Subnets"][0]["SubnetId"]
#     print("The Default Subnet : ", subnet_id)
#     return vpc_id, subnet_id

# def create_security_group():
#     ec2_client = boto3.client('ec2',
#                             "us-east-1",
#                             aws_access_key_id=cloudwatch_config.aws_access_key_id,
#                             aws_secret_access_key=cloudwatch_config.aws_secret_access_key)
#     sg_name = "memcache_security_group"
#     try:
#         vpc_id, subnet_id = grep_vpc_subnet_id()
#         response = ec2_client.create_security_group(
#             GroupName=sg_name,
#             Description="Memcache Security Group. This is created using python",
#             VpcId=vpc_id
#         )
#         sg_id = response["GroupId"]
#         print(sg_id)
#         sg_config = ec2_client.authorize_security_group_ingress(
#             GroupId=sg_id,
#             IpPermissions=[
#                 {
#                     'IpProtocol': 'tcp',
#                     'FromPort': 22,
#                     'ToPort': 22,
#                     'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
#                 }, {
#                     'IpProtocol': 'tcp',
#                     'FromPort': 5001,
#                     'ToPort': 5001,
#                     'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
#                 }, {
#                     'IpProtocol': 'tcp',
#                     'FromPort': 80,
#                     'ToPort': 80,
#                     'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
#                 }
#             ]
#         )
#         print(sg_config)
#         return sg_id, sg_name
#     except Exception as e:
#         if str(e).__contains__("already exists"):
#             response = ec2_client.describe_security_groups(GroupNames=[
#                                                                 sg_name])
#             sg_id = response["SecurityGroups"][0]["GroupId"]
#             print(sg_id, sg_name)
#             return sg_id, sg_name
        

    
    
    
    
    

        