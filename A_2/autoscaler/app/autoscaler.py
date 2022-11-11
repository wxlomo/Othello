from flask import request
from . import scaler
import memfunc
from memfunc import getAggregateMissRate1mins, start_ec2_instance, stop_ec2_instance, num_running
import time
import requests

missrate=0
run=0
MAXMISS=0.7
MINMISS=0.3
EXPAND=1
SHRINK=1

@scaler.before_first_request
# update every 1 mins
def updatestat():
    while True:
        time.sleep(60)
        response=requests.get("http://localhost:5002/auto")
        run=int(response.json())
        response=requests.get("http://localhost:5002/expand")
        EXPAND=int(response.json())
        response=requests.get("http://localhost:5002/shrink")
        SHRINK=int(response.json())
        response=requests.get("http://localhost:5002/max")
        MAXMISS=int(response.json())
        response=requests.get("http://localhost:5002/min")
        MINMISS=int(response.json())
        if (run):
            missrate=getAggregateMissRate1mins()
            num=num_running()
            if missrate>MAXMISS:
                new=max(8,int(num*EXPAND))
                add=new-num
                for i in range(add):
                    start_ec2_instance()
            elif missrate<MINMISS:
                new=max(1,int(num*SHRINK))
                add=num-new
                for i in range(add):
                    stop_ec2_instance()