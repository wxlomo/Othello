from flask import Flask
import datetime
from collections import OrderedDict

global memcache
global memcacheStatistics
global memcacheConfig

webapp = Flask(__name__)
memcache=OrderedDict()
memcacheConfig = {'capacity': 4,  
                  'policy': 'LRU'} # default setting, get real time config from db


class getResult:
    #store time and result (hit/miss) of a cache action
    def __init__(self, time, result):
        self.timestamp = time
        self.result = result
    
class cachestat:
    
    def __init__(self):
        self.getList = [] #store cache action results
        self.numberItems=0 #track number of items in cache
        self.currentSize = 0 #track current cache size
        self.requestList = [] #store all requests time
       
    def get_size(self):
        return self.currentSize
     
    def clear(self):
        self.currentSize = 0
        self.numberItems=0
        
    def addGetResult(self, result:getResult):
        """Add get() time and result to list
           argument is getResult(time of get, hit/miss)
        """
        self.getList.append(result)  
        
    def addRequestTime(self, t):
        """Add time of the request in requestList 
        argument is time of the request
        """
        self.requestList.append(t) 
        
    def addItem(self,size):
        self.currentSize+=size
        self.numberItems+=1
    
    def removeItem(self,size):
        self.currentSize-=size
        self.numberItems-=1
        
    def getStat(self):
        #get current statistics for the mem-cache over the past 10 minutes.

        total=0
        hit=0
        miss=0
        currentTime = datetime.datetime.now()
        startTime = currentTime - datetime.timedelta(minutes=10)
        newGetList = []
        for act in self.getList:
            if startTime <= act.timestamp:
                newGetList.append(act)
                if act.result == "miss":
                    miss = miss+1
                    total = total + 1
                if act.result == "hit":
                    hit = hit+1
                    total = total + 1
        hitRate = hit/total
        missRate = miss/total
        self.getList=newGetList
        
        numberRequests=0
        newRequestList=[]
        for t in self.requestList:
            if startTime <= t:
                numberRequests+=1
                newRequestList.append(t)
        self.requestList=newRequestList
        
        return [self.numberItems,self.currentSize,numberRequests, missRate ,hitRate]
memcacheStatistics = cachestat()

from app import main






