import time
import datetime
import boto3
import requests
import config
from config import awsKey


class Memcache():
    def __init__(self):
        self.instances = {}
        self.ami = "ami-080ff70d8f5b80ba5" 
        self.awsKey=awsKey
        self.VPCID='vpc-042054f0f945d031c'
        self.SubnetID='subnet-0c43635379007a839'
        self.SecurityGroupID='sg-0bd84a8e573f6d497'
    def refreshStateandIP(self, client):
        """
            Refresh instacne with current state from AWS.
        """
        # client = boto3.client('ec2', 
        #                     region_name='us-east-1',
        #                     aws_access_key_id=awsKey.aws_access_key_id,
        #                     aws_secret_access_key=awsKey.aws_secret_access_key)
        response = client.describe_instances()
        self.instances.clear()


        # print(response)
        for i in response["Reservations"]:
            if self.ami == i["Instances"][0]["ImageId"] and "Tags" in i["Instances"][0] and i["Instances"][0]["Tags"][0]["Value"].__contains__("ECE1779_A2_Memcache") and i["Instances"][0]["State"]["Name"] != 'terminated' and i["Instances"][0]["State"]["Name"] != 'shutting-down':
                
                memcacheName = i["Instances"][0]["Tags"][0]["Value"]
                memcacheNum = int(memcacheName[-1])
                

                self.instances[str(memcacheNum)] = {"Name": memcacheName,
                                                        "Status": i['Instances'][0]["State"]["Name"],
                                                        "instanceID": i['Instances'][0]['InstanceId'],
                                                        "amiID": self.ami,
                                                        "Number": memcacheNum,
                                                        "PublicIP": ""}

                if "PublicIpAddress" in i["Instances"][0].keys() and i["Instances"][0]["PublicIpAddress"]:
                    self.instances[str(memcacheNum)]["PublicIP"] = i["Instances"][0]["PublicIpAddress"]

        
        return True
            

    def init_ec2_instances(self):
        """
            MaxCount=1, # Keep the max count to 1, unless you have a requirement to increase it
            InstanceType="t2.micro", # Change it as per your need, But use the Free tier one
            KeyName="ECE1779_A2_public"
            :return: Creates the EC2 instance.
        """

        client = boto3.client('ec2', 
                            region_name='us-east-1',
                            aws_access_key_id=self.awsKey.aws_access_key_id,
                            aws_secret_access_key=self.awsKey.aws_secret_access_key)
        if not self.refreshStateandIP(client):
            print("Fail retirving state form aws. Abandoning operation.")
            return False
        # Start exist instances:
        
        for instance in self.instances.values():
            if instance["Status"]=='stopped':
                client.start_instances(InstanceIds=[instance["instanceID"]])
                
        
        # Create instance instance and have not reach maximum memcaches (8):
        
        

            
        memcacheName = ("ECE1779_A2_Memcache_" +
                        str(0))
        for i in range(8):
            if str(i) not in self.instances.keys():
                
                memcacheName = ("ECE1779_A2_Memcache_" +
                                str(i))


                new = client.run_instances(

                    ImageId=self.ami,
                    MinCount=1,
                    MaxCount=1,
                    InstanceType="t2.micro",
                    KeyName="ECE1779_A2_public",
                    SecurityGroupIds=[self.SecurityGroupID],
                    SubnetId=self.SubnetID,
                    TagSpecifications=[{'ResourceType': 'instance',
                                        'Tags': [
                                            {
                                                'Key': 'Name',
                                                'Value': memcacheName
                                            },
                                        ]
                                        }]

                )
                

                self.instances[str(i)] =   {"Name": memcacheName,
                                            "Status": new['Instances'][0]["State"]["Name"],
                                            "instanceID": new['Instances'][0]['InstanceId'],
                                            "amiID": self.ami,
                                            "Number": i,
                                            "PublicIP": ""}
        for i in range(8):
            while self.instances[str(i)]["Status"]!="running" and self.instances[str(i)]["PublicIP"] != "":
                self.refreshStateandIP(client) 
            address="http://"+str(self.instances[str(i)]["PublicIP"])+":5001/memIndex/"+str(i)
            response = requests.get(address)          
            
        return True
        
    def start_ec2_instance(self):
        for i in range(8):
            if self.instances[str(i)]["Activate"]=='False':
                self.instances[str(i)]["Activate"]='True'
                return('OK')
                break
            elif i==7:
                return("Alreade 8 memcache running")
        
        
            
    def stop_ec2_instance(self):
        for i in range(7):
            if self.instances[str(i)]["Activate"]=='True' and self.instances[str(i+1)]["Activate"]=='False':
                self.instances[str(i)]["Activate"]='False'
                break
            elif i==6:
                i=7
                self.instances[str(i)]["Activate"]='False'
                break
        
        ip=self.get_nth_ip(i)
        address="http://"+str(ip)+":5001/clear"
        response = requests.get(address)            

    def end_ec2_instances(self):
        """
            Stop memcache with the LARGEST number.
            Note that you should wait for some time for the memcache EC2 to shutdown before it shows up.
        """
        if self.instances:
            client = boto3.client('ec2', 
                            region_name='us-east-1',
                            aws_access_key_id=self.awsKey.aws_access_key_id,
                            aws_secret_access_key=self.awsKey.aws_secret_access_key)
            if not self.refreshStateandIP(client):
                print("Fail retirving state form aws. Abandoning operation.")
                return "ERROR! Fail retirving state form aws. Abandoning operation."
            # Check what is the last num
            
            for instance in self.instances.values():
                instance["Activate"]='False'
                if instance["Status"]=='running':
                    client.stop_instances(InstanceIds=[instance["instanceID"]])
            
        return "OK"

    def get_all_ip(self):
        """Returns all known IPs of all EC2 memcaches for frontend to use."""
        ipList = []
        if not self.refreshStateandIP():
            print("Fail retirving state form aws. Abandoning operation.")
            return
        if self.instances:
            for instance in self.instances.values():
                if instance["Status"]=="running" and instance["PublicIP"] != "": # and instance["Activate"]=="True"
                    ipList.append(instance["PublicIP"])
        return ipList

    def get_nth_ip(self,n):
        if not self.refreshStateandIP():
            print("Fail retirving state form aws. Abandoning operation.")
            return
        if self.instances[str(n)]["Status"]=="running" and self.instances[str(n)]["Activate"]=="True"and self.instances[str(n)]["PublicIP"] != "":
            return self.instances[str(n)]["PublicIP"]
        return "Error! Failed retrive ip"
    def num_running(self):
        for i in range(8):
            if self.instances[str(i)]["Activate"]=='False':
                break
        return int(i)






def getAggregateMissRate1mins(intervals=60, period=60):
    client = boto3.client('cloudwatch', 
                            region_name='us-east-1',
                            aws_access_key_id=awsKey.aws_access_key_id,
                            aws_secret_access_key=awsKey.aws_secret_access_key)
    startTime = datetime.datetime.utcnow() - datetime.timedelta(seconds=intervals)
    endTime = datetime.datetime.utcnow()
    miss = 0
    total= 0
    for i in range(8):
        
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
    
    
def getAggregateStat30Mins():
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
    for j in range (30,1,-1):
        startTime = now - datetime.timedelta(minutes=i)
        endTime = now - datetime.timedelta(minutes=i-1)
        miss = 0
        total= 0
        for i in range(8):
            
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
    return [numberItems, currentSize, totalRequests, missRate, hitRate]
