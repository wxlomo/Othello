import random
import sys
from collections import OrderedDict
from flask import request, g
from app import webapp 
from flask import json
import datetime
import mysql.connector
import threading
import time
from app import DBconfig

global cache
global memcacheStatistics
global memcacheConfig



cache=OrderedDict()
memcacheConfig = {'capacity': 4,  
                  'policy': 'LRU'} # default setting, get real time config from db


def get_db():
    """Establish the connection to the database.

    Args:
      n/a

    Returns:
      MySQLConnection: the connector to the available database.
    """
    
    dbconnect = mysql.connector.connect(
                user=DBconfig.db_config['user'],
                password=DBconfig.db_config['password'],
                host=DBconfig.db_config['host'],
                database=DBconfig.db_config['database']
            )
        

    return dbconnect





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
        hitRate=0
        missRate=0
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
        if(total!=0):
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
        
        return [self.numberItems,self.currentSize/1024/1024,numberRequests, missRate ,hitRate]
memcacheStatistics = cachestat()





@webapp.route('/')
def page():
    return "Started successfully"
    
@webapp.before_first_request
def threadedUpdate():
    
    thread = threading.Thread(target=updatestat)
    thread.start()
    
def updatestat():
    while True:
        time.sleep(5)
        statistic()

@webapp.route('/clear')
def clearCache():
    t=datetime.datetime.now()
    memcacheStatistics.addRequestTime(t)
    
    cache.clear()
    memcacheStatistics.clear()
    response = webapp.response_class(
        response=json.dumps("OK"),
        status=200,
        mimetype='application/json'
    )
    return response
    
@webapp.route('/invalidateKey/<key>')   
def invalidateKey(key):
    t=datetime.datetime.now()
    memcacheStatistics.addRequestTime(t)
    if key in cache:
        value = cache[key]
        size=sys.getsizeof(value)
        memcacheStatistics.removeItem(size)
        del cache[key]
        response = webapp.response_class(
            response=json.dumps("OK"),
            status=200,
            mimetype='application/json'
        )
        
    else:
        response = webapp.response_class(
            response=json.dumps("Unknown key"),
            status=400,
            mimetype='application/json'
        )
        
    return response
    
    
    
@webapp.route('/refreshConfiguration')   
def refreshConfiguration():
    t=datetime.datetime.now()
    memcacheStatistics.addRequestTime(t)
    cnx = get_db()
    
    cursor = cnx.cursor()
    query =  "SELECT capacity, lru FROM ece1779.memcache_config WHERE userid = 1;"
    cursor.execute(query)
    capacity, policy = cursor.fetchone()
    
    memcacheConfig['capacity'] = int(capacity)
    if str(policy)=='lru':
        memcacheConfig[policy] = 'LRU'
    else:
        memcacheConfig[policy] = 'Random'
    
    
    
    cursor.close()
    cnx.close()
    while (memcacheStatistics.get_size() > memcacheConfig['capacity']*1024*1024):
        if memcacheConfig['policy'] == 'LRU':
            delvalue=cache.popitem(False)[1]
            size=sys.getsizeof(delvalue)
            memcacheStatistics.removeItem(size)
        else:
            delkey=random.choice(list(cache.keys()))
            delvalue = cache[delkey]
            size=sys.getsizeof(delvalue)
            memcacheStatistics.removeItem(size)
            del cache[delkey]
    response = webapp.response_class(
        response=json.dumps("OK"),
        status=200,
        mimetype='application/json'
        )
    return response
    
    
@webapp.route('/get',methods=['POST'])
def get():
    t=datetime.datetime.now()
    memcacheStatistics.addRequestTime(t)
    
    key = request.form.get('key')
    if key in cache:
        value = cache[key]
        r=getResult(t, 'hit')
        memcacheStatistics.addGetResult(r)
        
        if memcacheConfig['policy'] == 'LRU':
            cache.move_to_end(key) 
            
        response = webapp.response_class(
            response=json.dumps(value),
            status=200,
            mimetype='application/json'
        )
    else:
        r=getResult(t, 'miss')
        memcacheStatistics.addGetResult(r)
        response = webapp.response_class(
            response=json.dumps("Unknown key"),
            status=400,
            mimetype='application/json'
        )

    return response

@webapp.route('/put',methods=['POST']) 
def put():
   
    t=datetime.datetime.now()
    memcacheStatistics.addRequestTime(t)
    
    key = request.form.get('key')
    value = request.form.get('value')
    image_size = sys.getsizeof(value)
    if key in cache:
        delvalue = cache[key]
        size=sys.getsizeof(delvalue)
        memcacheStatistics.removeItem(size)
        del cache[key]
    if image_size > memcacheConfig['capacity']*1024*1024:
        response = webapp.response_class(
        response=json.dumps("Image too big to cache"),
        status=200,
        mimetype='application/json'
        )
        return response
    
    while (image_size + memcacheStatistics.get_size() > memcacheConfig['capacity']*1024*1024):
        if memcacheConfig['policy'] == 'LRU':
            delvalue=cache.popitem(False)[1]
            size=sys.getsizeof(delvalue)
            memcacheStatistics.removeItem(size)
        else:
            delkey=random.choice(list(cache.keys()))
            delvalue = cache[key]
            size=sys.getsizeof(delvalue)
            memcacheStatistics.removeItem(size)
            del cache[delkey]
            
    cache[key] = value
    memcacheStatistics.addItem(image_size)
    if memcacheConfig['policy'] == 'LRU':
        cache.move_to_end(key) 
        
    response = webapp.response_class(
        response=json.dumps("OK"),
        status=200,
        mimetype='application/json'
    )

    return response


@webapp.route('/statistic') 
def statistic():
    s=memcacheStatistics.getStat()
    
    cnx = get_db()
    cursor = cnx.cursor()
    query =  "UPDATE ece1779.memcache_stat SET itemNum = %s, totalSize = %s, requestNum = %s, missRate = %s, hitRate = %s WHERE userid = 1;"
    cursor.execute(query,s)
    
    cnx.commit()
    cursor.close()
    cnx.close()
    
    response = webapp.response_class(
        response=json.dumps('OK'),
        status=200,
        mimetype='application/json'
    )

    return response