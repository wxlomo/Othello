import time
import datetime
import boto3
import requests
from . import config
#from config import awsKey
awsKey = config.awsKey


import hashlib

instances = {}
ami = "ami-01f8d4934ffdf367e" 
VPCID='vpc-042054f0f945d031c'
SubnetID='subnet-0c43635379007a839'
SecurityGroupID='sg-0bd84a8e573f6d497'
user_data_script="""
Content-Type: text/x-shellscript; charset="us-ascii"
#!/bin/bash
cd ECE1779-Group9-Project-Code/A_2/memcache && gunicorn --bind 0.0.0.0:5001 --workers 1 run:mem
--//
"""
def refreshStateandIP(client):
    """
        Refresh instacne with current state from AWS.
    """

    response = client.describe_instances()
    instances.clear()



    for i in response["Reservations"]:
        if ami == i["Instances"][0]["ImageId"] and "Tags" in i["Instances"][0] and i["Instances"][0]["Tags"][0]["Value"].__contains__("ECE1779_A2_Memcache") and i["Instances"][0]["State"]["Name"] != 'terminated' and i["Instances"][0]["State"]["Name"] != 'shutting-down':
            
            memcacheName = i["Instances"][0]["Tags"][0]["Value"]
            memcacheNum = int(memcacheName[-1])
            

            instances[str(memcacheNum)] = {"Name": memcacheName,
                                                    "Status": i['Instances'][0]["State"]["Name"],
                                                    "instanceID": i['Instances'][0]['InstanceId'],
                                                    "amiID": ami,
                                                    "Number": memcacheNum,
                                                    "PublicIP": ""}

            if "PublicIpAddress" in i["Instances"][0].keys() and i["Instances"][0]["PublicIpAddress"]:
                instances[str(memcacheNum)]["PublicIP"] = i["Instances"][0]["PublicIpAddress"]

    
    return True
        
#use before manager first request @manager.before_first_request
def init_ec2_instances():
    """
        MaxCount=1, # Keep the max count to 1, unless you have a requirement to increase it
        InstanceType="t2.micro", # Change it as per your need, But use the Free tier one
        KeyName="ECE1779_A2_public"
        :return: Creates the EC2 instance.
    """

    client = boto3.client('ec2', 
                        region_name='us-east-1',
                        aws_access_key_id=awsKey['aws_access_key_id'],
                        aws_secret_access_key=awsKey['aws_secret_access_key'])
    if not refreshStateandIP(client):
        print("Fail retirving state form aws. Abandoning operation.")
        return False
    # Start exist instances:
    
    for instance in instances.values():
        if instance["Status"]=='stopped':
            client.start_instances(InstanceIds=[instance["instanceID"]])
            
    
    # Create instance instance and have not reach maximum memcaches (8):
    
    memcacheName = ("ECE1779_A2_Memcache_" +
                    str(0))
    for i in range(8):
        if str(i) not in instances.keys():
            
            memcacheName = ("ECE1779_A2_Memcache_" +
                            str(i))


            new = client.run_instances(

                ImageId=ami,
                MinCount=1,
                MaxCount=1,
                InstanceType="t2.micro",
                # KeyName="ECE1779_A2_public",
                SecurityGroupIds=[SecurityGroupID],
                SubnetId=SubnetID,
                # UserData=user_data_script,
                TagSpecifications=[{'ResourceType': 'instance',
                                    'Tags': [
                                        {
                                            'Key': 'Name',
                                            'Value': memcacheName
                                        },
                                    ]
                                    }]

            )
            

            instances[str(i)] =   {"Name": memcacheName,
                                        "Status": new['Instances'][0]["State"]["Name"],
                                        "instanceID": new['Instances'][0]['InstanceId'],
                                        "amiID": ami,
                                        "Number": i,
                                        "PublicIP": ""}
    for i in range(8):
        while instances[str(i)]["Status"]!="running" and instances[str(i)]["PublicIP"] == "":
            refreshStateandIP(client) 
        instances[str(i)]["Activate"]='False'
        address="http://"+str(instances[str(i)]["PublicIP"])+":5001/memIndex/"+str(i)
        response = requests.get(address)          
        
    return True
    
    
    
# @manager.route('/start')  run this func

def start_ec2_instance():
    for i in range(8):
        if instances[str(i)]["Activate"]=='False':
            instances[str(i)]["Activate"]='True'
            redirectCache()
            return('OK')
            break
        elif i==7:
            return("Alreade 8 memcache running")
    
    
# @manager.route('/stop')       run this func
def stop_ec2_instance():
    for i in range(7):
        if instances[str(i)]["Activate"]=='True' and instances[str(i+1)]["Activate"]=='False':
            instances[str(i)]["Activate"]='False'
            break
        elif i==6:
            i=7
            instances[str(i)]["Activate"]='False'
            break
    redirectCache()
    ip=get_nth_ip(i)
    print(ip)
    requests.get("http://"+str(ip)+":5001/clear")
              
#use when manager end
def end_ec2_instances():
    """
        Stop memcache with the LARGEST number.
        Note that you should wait for some time for the memcache EC2 to shutdown before it shows up.
    """
    if instances:
        client = boto3.client('ec2', 
                        region_name='us-east-1',
                        aws_access_key_id=awsKey['aws_access_key_id'],
                        aws_secret_access_key=awsKey['aws_secret_access_key'])
        if not refreshStateandIP(client):
            print("Fail retirving state form aws. Abandoning operation.")
            return "ERROR! Fail retirving state form aws. Abandoning operation."
        # Check what is the last num
        
        for instance in instances.values():
            instance["Activate"]='False'
            if instance["Status"]=='running':
                client.stop_instances(InstanceIds=[instance["instanceID"]])
        
    return "OK"

# use to update memcache config
def get_all_ip():
    """Returns all known IPs of all EC2 memcaches for frontend to use."""
    ipList = []

    if instances:
        for instance in instances.values():
            if instance["Status"]=="running"  and instance["PublicIP"] != "": #and instance["Activate"]=="True"
                ipList.append(instance["PublicIP"])
    return ipList

# @manager.route('/ip/<n>')  response the return of this func
def get_nth_ip(n):

    if instances[str(n)]["Status"]=="running" and instances[str(n)]["PublicIP"] != "": #instances[str(n)]["Activate"]=="True"
        return instances[str(n)]["PublicIP"]
    return "Error! Failed retrive ip"

# @manager.route('/numrunning')  response the return of this func
def num_running():
    for i in range(8):
        if instances[str(i)]["Activate"]=='False':
            return int(i)
            break
    return 8





# @manager.route('/1minmiss')  response the return of this func
def getAggregateMissRate1mins(intervals=60, period=60):
    client = boto3.client('cloudwatch', 
                            region_name='us-east-1',
                            aws_access_key_id=awsKey['aws_access_key_id'],
                            aws_secret_access_key=awsKey['aws_secret_access_key'])
    startTime = datetime.datetime.utcnow() - datetime.timedelta(seconds=intervals)
    endTime = datetime.datetime.utcnow()
    miss = 0
    total= 0
    for i in range(8):
        
        response=client.get_metric_statistics(
                Namespace='ece1779/memcache',
                MetricName='miss',
                Dimensions=[{
                        "Name": "instance",
                        "Value": str(i)
                    }],
                StartTime = startTime,
                EndTime = endTime,
                Period=60,
                Statistics=['Sum'],
                Unit='Count',
                )
        if response['Datapoints']:
            miss+=response['Datapoints'][0]['Sum']
        response=client.get_metric_statistics(
                Namespace='ece1779/memcache',
                MetricName='total',
                Dimensions=[{
                        "Name": "instance",
                        "Value": str(i)
                    }],
                StartTime = startTime,
                EndTime = endTime,
                Period=60,
                Statistics=['Sum'],
                Unit='Count',
                )
        if response['Datapoints']:
            total+=response['Datapoints'][0]['Sum']
        totald=total
        if total==0:
            totald=1    
    return miss/totald
    
    
def getAggregateStat30Mins():
    numberItems=[]
    currentSize=[]
    totalRequests=[]
    missRate=[]
    hitRate=[]
    client = boto3.client('cloudwatch', 
                        region_name='us-east-1',
                        aws_access_key_id=awsKey['aws_access_key_id'],
                        aws_secret_access_key=awsKey['aws_secret_access_key'])
    now=datetime.datetime.utcnow()
    for j in range (31,1,-1):
        startTime = now - datetime.timedelta(minutes=j)
        endTime = now - datetime.timedelta(minutes=j-1)
        miss = 0
        total= 0
        numItem=0
        size=0
        for i in range(8):
            
            
            response=client.get_metric_statistics(
                    Namespace='ece1779/memcache',
                    MetricName='miss',
                    Dimensions=[{
                            "Name": "instance",
                            "Value": str(i)
                        }],
                    StartTime = startTime,
                    EndTime = endTime,
                    Period=60,
                    Statistics=['Sum'],
                    Unit='Count',
                    )
            if response['Datapoints']:
                miss+=response['Datapoints'][0]['Sum']
            response=client.get_metric_statistics(
                    Namespace='ece1779/memcache',
                    MetricName='numberRequests',
                    Dimensions=[{
                            "Name": "instance",
                            "Value": str(i)
                        }],
                    StartTime = startTime,
                    EndTime = endTime,
                    Period=60,
                    Statistics=['Sum'],
                    Unit='Count',
                    )
            if response['Datapoints']:
                total+=response['Datapoints'][0]['Sum']
            response=client.get_metric_statistics(
                    Namespace='ece1779/memcache',
                    MetricName='numberItems',
                    Dimensions=[{
                            "Name": "instance",
                            "Value": str(i)
                        }],
                    StartTime = startTime,
                    EndTime = endTime,
                    Period=60,
                    Statistics=['Average'],
                    Unit='Count',
                    )
            if response['Datapoints']:
                numItem+=response['Datapoints'][0]['Average']
            
            response=client.get_metric_statistics(
                    Namespace='ece1779/memcache',
                    MetricName='currentSize',
                    Dimensions=[{
                            "Name": "instance",
                            "Value": str(i)
                        }],
                    StartTime = startTime,
                    EndTime = endTime,
                    Period=60,
                    Statistics=['Average'],
                    Unit='Megabits',
                    )
            if response['Datapoints']:
                size+=response['Datapoints'][0]['Average']
        totald=total
        if total==0:
            totald=1
        
        missRate.append(float(miss/totald))
        hitRate.append(1.0-miss/totald)
        totalRequests.append(total)
        numberItems.append(numItem)
        currentSize.append(size)
    return [numberItems, currentSize, totalRequests, missRate, hitRate]
        

        

    
    
def redirectCache():
    iplist=get_all_ip()
    n = num_running()
    caches=[]
    if n !=0:
        for ip in iplist:
            address="http://"+str(ip)+":5001/getall"
            response = requests.post(address)
            if response.json()!="Empty":
                caches.append(response.json())
        for cache in caches:
            redirect(n,cache)        
    
    

def redirect(n,cache):
    
    for key in cache:
        request_partition = int(hashlib.md5(key.encode()).hexdigest(), 16) // 0x10000000000000000000000000000000
        request_pooling = request_partition % n
        ip=get_nth_ip(request_pooling)
        data = {'key': key, 'value': cache[key]}
        address="http://"+str(ip)+":5001/put"
        response = requests.post(address, data=data)
        # result = hashlib.md5(key.encode()).hexdigest()
        # if result < 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF:
        #     partition=0
        # elif result < 0x1FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF:
        #     partition=1
        # elif result < 0x2FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF:
        #     partition=2
        # elif result < 0x3FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF:
        #     partition=3
        # elif result < 0x4FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF:
        #     partition=4
        # elif result < 0x5FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF:
        #     partition=5
        # elif result < 0x6FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF:
        #     partition=6
        # elif result < 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF:
        #     partition=7
        # elif result < 0x8FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF:
        #     partition=8
        # elif result < 0x9FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF:
        #     partition=9
        # elif result < 0xAFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF:
        #     partition=10
        # elif result < 0xBFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF:
        #     partition=11
        # elif result < 0xCFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF:
        #     partition=12
        # elif result < 0xDFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF:
        #     partition=13
        # elif result < 0xEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF:
        #     partition=14
        # else: #result < 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        #     partition=15
        
          