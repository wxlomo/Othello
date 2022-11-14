from flask import request
from . import scaler
import time
import requests  
import threading
# import os
# import sys

# sys.path.append(os.path.abspath('C:/Users/Haozhe Sun/Desktop/ECE1779-Group9-Project-Code/A_2/memfunc'))
# import memfunc
# from memfunc import Memcache


missrate=0
run=0
MAXMISS=0.7
MINMISS=0.3
EXPAND=1
SHRINK=1

@scaler.before_first_request
def threadedUpdate():
    thread = threading.Thread(target=updatestat)
    thread.start()
    
# update every 1 mins
def updatestat():

    while True:
        time.sleep(60)
        response=requests.get("http://localhost:5002/scalerconfig")
        result=response.json()
        run=int(result['scalerswitch'])
        
        EXPAND=float(result['expand'])
        
        SHRINK=float(result['shrink'])
        
        MAXMISS=float(result['maxrate'])
        
        MINMISS=float(result['minrate'])
        if (run):
            response=requests.get("http://localhost:5002/1minmiss")
            missrate=float(response.json())
            response=requests.get("http://localhost:5002/numrunning")
            num=int(response.json())
            if missrate>MAXMISS:
                new=max(8,int(num*EXPAND))
                if new<8 and new==num:
                    new+=1
                add=new-num
                for i in range(add):
                    response=requests.get("http://localhost:5002/start")
            elif missrate<MINMISS:
                new=max(1,int(num*SHRINK))
                if new>1 and new==num:
                    new-=1
                add=num-new
                for i in range(add):
                    response=requests.get("http://localhost:5002/stop")
                    
@scaler.route('/')
# status page render
def page():
    return "Scaler Is Ready"