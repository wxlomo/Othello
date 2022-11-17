import random
import sys
import datetime
import mysql.connector
import threading
import time

from collections import OrderedDict
from flask import request, g
from . import mem,config

from flask import jsonify,json
import boto3
global cache
global memcacheStatistics
global memcacheConfig
awsKey=config.awsKey
cache = OrderedDict()
memcacheConfig = {'capacity': 4,
                  'policy': 'LRU'}  # default setting, get real time config from db


# def get_db():
#     dbconnect = mysql.connector.connect(
#         user=dbconfig.db_config['user'],
#         password=dbconfig.db_config['password'],
#         host=dbconfig.db_config['host'],
#         database=dbconfig.db_config['database']
#     )
#     return dbconnect


# store time and result (hit/miss) of a cache action
class getResult:
    def __init__(self, time, result):
        self.timestamp = time
        self.result = result


class cachestat:
    def __init__(self):
        self.getList = []  # store cache action results
        self.numberItems = 0  # track number of items in cache
        self.currentSize = 0  # track current cache size
        self.requestList = []  # store all requests time
        self.index=-1
    def get_size(self):
        return self.currentSize

    def clear(self):
        self.currentSize = 0
        self.numberItems = 0

    # Add get() time and result to list
    # argument is getResult(time of get, hit/miss)
    def addGetResult(self, result: getResult):
        self.getList.append(result)

    # Add time of the request in requestList
    # argument is time of the request
    def addRequestTime(self, t):
        self.requestList.append(t)

    def addItem(self, size):
        self.currentSize += size
        self.numberItems += 1

    def removeItem(self, size):
        self.currentSize -= size
        self.numberItems -= 1

    # get current statistics for the mem-cache over the past 10 minutes.
    def get10MinStat(self):
        total = 0
        hit = 0
        miss = 0
        hitRate = 0
        missRate = 0
        currentTime = datetime.datetime.now()
        startTime = currentTime - datetime.timedelta(minutes=10)
        newGetList = []
        for act in self.getList:
            if startTime <= act.timestamp:
                newGetList.append(act)
                if act.result == "miss":
                    miss = miss + 1
                    total = total + 1
                if act.result == "hit":
                    hit = hit + 1
                    total = total + 1
        if total != 0:
            hitRate = hit / total
            missRate = miss / total
        self.getList = newGetList

        # numberRequests = 0
        # newRequestList = []
        # for t in self.requestList:
        #     if startTime <= t:
        #         numberRequests += 1
        #         newRequestList.append(t)
        # self.requestList = newRequestList
        return [self.numberItems, self.currentSize / 1024 / 1024, total, missRate, hitRate,self.index]

    def get1MinStat(self):
        total = 0
        hit = 0
        miss = 0
        hitRate = 0
        missRate = 0
        currentTime = datetime.datetime.now()
        startTime = currentTime - datetime.timedelta(minutes=1)
        newGetList = []
        for act in self.getList:
            if startTime <= act.timestamp:
                newGetList.append(act)
                if act.result == "miss":
                    miss = miss + 1
                    total = total + 1
                if act.result == "hit":
                    hit = hit + 1
                    total = total + 1
        if total != 0:
            hitRate = hit / total
            missRate = miss / total
        self.getList = newGetList

        
        return [self.numberItems, self.currentSize / 1024 / 1024, total, missRate, hitRate,self.index]
    
    def get5SecStat(self):
        total = 0
        miss = 0
        hitRate = 0
        missRate = 0
        currentTime = datetime.datetime.now()
        startTime = currentTime - datetime.timedelta(seconds=5)
        newGetList = []
        for act in self.getList:
            if startTime <= act.timestamp:
                newGetList.append(act)
                if act.result == "miss":
                    miss = miss + 1
                total = total + 1
                
        if total != 0:
            missRate = miss / total
        self.getList = newGetList

        
        return [self.numberItems, self.currentSize / 1024 / 1024, total, missRate*100, miss,self.index]

memcacheStatistics = cachestat()


@mem.route('/')
# status page render
def page():
    return "Memcache Is Ready"


@mem.before_first_request
# create the thread to keep updating the statistics
def threadedUpdate():
    thread = threading.Thread(target=updatestat)
    thread.start()


# update the statistics in every 5 seconds
def updatestat():
    while True:
        time.sleep(5)
        statistic5secs()


@mem.route('/clear')
# clear the memcache
def clearCache():
    # t = datetime.datetime.now()
    # memcacheStatistics.addRequestTime(t)

    cache.clear()
    memcacheStatistics.clear()
    response = mem.response_class(
        response=json.dumps("OK"),
        status=200,
        mimetype='application/json'
    )
    return response


@mem.route('/invalidateKey/<key>')
# invalidate the designated key in memcache
def invalidateKey(key):
    # t = datetime.datetime.now()
    # memcacheStatistics.addRequestTime(t)
    if key in cache:
        value = cache[key]
        size = sys.getsizeof(value)
        memcacheStatistics.removeItem(size)
        del cache[key]
        response = mem.response_class(
            response=json.dumps("OK"),
            status=200,
            mimetype='application/json'
        )

    else:
        response = mem.response_class(
            response=json.dumps("Unknown key"),
            status=400,
            mimetype='application/json'
        )

    return response


@mem.route('/refreshConfiguration/<capacity>/<policy>')
# reload the configurations from database after frontend update it
def refreshConfiguration(capacity, policy):
    # t = datetime.datetime.now()
    # memcacheStatistics.addRequestTime(t)
    # cnx = get_db()

    # cursor = cnx.cursor()
    # query = "SELECT capacity, lru FROM gallery.memcache_config WHERE userid = 1;"
    # cursor.execute(query)
    # capacity, policy = cursor.fetchone()

    memcacheConfig['capacity'] = int(capacity)
    if str(policy) == 'lru':
        memcacheConfig[policy] = 'LRU'
    else:
        memcacheConfig[policy] = 'Random'

    # cursor.close()
    # cnx.close()
    while (memcacheStatistics.get_size() > memcacheConfig['capacity'] * 1024 * 1024):
        if memcacheConfig['policy'] == 'LRU':
            delvalue = cache.popitem(False)[1]
            size = sys.getsizeof(delvalue)
            memcacheStatistics.removeItem(size)
        else:
            delkey = random.choice(list(cache.keys()))
            delvalue = cache[delkey]
            size = sys.getsizeof(delvalue)
            memcacheStatistics.removeItem(size)
            del cache[delkey]
    response = mem.response_class(
        response=json.dumps("OK"),
        status=200,
        mimetype='application/json'
    )
    return response


@mem.route('/get', methods=['POST'])
# send the image retrieved from the given key to the frontend
def get():
    t = datetime.datetime.now()
    # memcacheStatistics.addRequestTime(t)

    key = request.form.get('key')
    if key in cache:
        value = cache[key]
        r = getResult(t, 'hit')
        memcacheStatistics.addGetResult(r)

        if memcacheConfig['policy'] == 'LRU':
            cache.move_to_end(key)

        response = mem.response_class(
            response=json.dumps(value),
            status=200,
            mimetype='application/json'
        )
    else:
        r = getResult(t, 'miss')
        memcacheStatistics.addGetResult(r)
        response = mem.response_class(
            response=json.dumps("Unknown key"),
            status=400,
            mimetype='application/json'
        )

    return response



@mem.route('/getall', methods=['POST'])
# send the image retrieved from the given key to the frontend
def getall():
    # t = datetime.datetime.now()
    # memcacheStatistics.addRequestTime(t)

    
    if cache:
        return cache
    else:
        response = mem.response_class(
                response=json.dumps("Empty"),
                status=400,
                mimetype='application/json'
            )

    return response

@mem.route('/put', methods=['POST'])
# put an image and its key to memcache
def put():
    # t = datetime.datetime.now()
    # memcacheStatistics.addRequestTime(t)

    key = request.form.get('key')
    value = request.form.get('value')
    image_size = sys.getsizeof(value)
    if key in cache:
        delvalue = cache[key]
        size = sys.getsizeof(delvalue)
        memcacheStatistics.removeItem(size)
        del cache[key]
    if image_size > memcacheConfig['capacity'] * 1024 * 1024:
        response = mem.response_class(
            response=json.dumps("Image too big to cache"),
            status=200,
            mimetype='application/json'
        )
        return response

    while image_size + memcacheStatistics.get_size() > memcacheConfig['capacity'] * 1024 * 1024:
        if memcacheConfig['policy'] == 'LRU':
            delvalue = cache.popitem(False)[1]
            size = sys.getsizeof(delvalue)
            memcacheStatistics.removeItem(size)
        else:
            delkey = random.choice(list(cache.keys()))
            delvalue = cache[key]
            size = sys.getsizeof(delvalue)
            memcacheStatistics.removeItem(size)
            del cache[delkey]

    cache[key] = value
    memcacheStatistics.addItem(image_size)
    if memcacheConfig['policy'] == 'LRU':
        cache.move_to_end(key)

    response = mem.response_class(
        response=json.dumps("OK"),
        status=200,
        mimetype='application/json'
    )

    return response


@mem.route('/statistic')
# update the statistic data to database
def statistic5secs():
    # s = memcacheStatistics.getStat()

    # cnx = get_db()
    # cursor = cnx.cursor()
    # query = "UPDATE gallery.memcache_stat SET itemNum = %s, totalSize = %s, requestNum = %s, missRate = %s, hitRate = %s WHERE userid = 1;"
    # cursor.execute(query, s)

    # cnx.commit()
    # cursor.close()
    # cnx.close()

    # response = mem.response_class(
    #     response=json.dumps('OK'),
    #     status=200,
    #     mimetype='application/json'
    # )
    # return response
    numberItems, currentSize, total, missRate, miss,index = memcacheStatistics.get5SecStat()
    client = boto3.client('cloudwatch', 
                            region_name='us-east-1',
                            aws_access_key_id=awsKey['aws_access_key_id'],
                            aws_secret_access_key=awsKey['aws_secret_access_key'])
    response = client.put_metric_data(
            MetricData = [{
                    'MetricName': 'numberItems',
                    'Dimensions': [{
                            'Name': 'instance',
                            'Value': str(index)
                        }],
                    'Unit': 'Count',
                    'Value': numberItems}],
            Namespace = 'ece1779/memcache')
    
    response = client.put_metric_data(
            MetricData = [{
                    'MetricName': 'currentSize',
                    'Dimensions': [{
                            'Name': 'instance',
                            'Value': str(index)
                        }],
                    'Unit': 'Megabits',
                    'Value': currentSize}],
            Namespace = 'ece1779/memcache')
    
    response = client.put_metric_data(
            MetricData = [{
                    'MetricName': 'numberRequests',
                    'Dimensions': [{
                            'Name': 'instance',
                            'Value': str(index)
                        }],
                    'Unit': 'Count',
                    'Value': total}],
            Namespace = 'ece1779/memcache')
    
    response = client.put_metric_data(
            MetricData = [{
                    'MetricName': 'miss',
                    'Dimensions': [{
                            'Name': 'instance',
                            'Value': str(index)
                        }],
                    'Unit': 'Count',
                    'Value': miss}],
            Namespace = 'ece1779/memcache')
    
    response = client.put_metric_data(
            MetricData = [{
                    'MetricName': 'missRate',
                    'Dimensions': [{
                            'Name': 'instance',
                            'Value': str(index)
                        }],
                    'Unit': 'Percent',
                    'Value': missRate}],
            Namespace = 'ece1779/memcache')
    
    response = client.put_metric_data(
            MetricData = [{
                    'MetricName': 'hitRate',
                    'Dimensions': [{
                            'Name': 'instance',
                            'Value': str(index)
                        }],
                    'Unit': 'Percent',
                    'Value': 100.0-missRate}],
            Namespace = 'ece1779/memcache')
    return response
    
@mem.route('/memIndex/<id>')
def setIndex(id):
    

    memcacheStatistics.index = int(id)

    return jsonify({"success": "true",
                    "statusCode": 200})
    
