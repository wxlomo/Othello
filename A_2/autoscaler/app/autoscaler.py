from flask import request
from . import scaler
import time
import requests  
import threading


# create thread for auto scale
@scaler.before_first_request
def threadedUpdate():
    thread1 = threading.Thread(target=auto)
    thread1.start()


# scale every 1 mins
def auto():
    while True: 
        time.sleep(60)
        autoscale()


# scale
@scaler.route('/autonow')
def autoscale():
    # Get autoscaler setting from manager
    response = requests.get("http://localhost:5002/scalerconfig")
    result = response.json()
    run = int(result['scalerswitch'])
    EXPAND = float(result['expand'])
    SHRINK = float(result['shrink'])
    MAXMISS = float(result['maxrate'])
    MINMISS = float(result['minrate'])
    # run if autoscaler is set to be on
    if run:
        # request 1 mins miss rate from manager to make decision
        response = requests.get("http://localhost:5002/1minmiss")
        missrate = float(response.json())
        # request number of current running memcache nodes
        response = requests.get("http://localhost:5002/numrunning")
        num = int(response.json())
        new = num
        # if miss rate greater than Max miss rate, grow
        if missrate > MAXMISS:
            new = min(8, int(num*EXPAND))
            if new < 8 and new == num:
                new += 1
            add = new-num
            for i in range(add):
                response = requests.get("http://localhost:5002/startinstance")
                scaler.logger.debug(response.text)
        # if miss rate less than min miss rate, shrink
        elif missrate < MINMISS:
            new = max(1, int(num*SHRINK))
            if new > 1 and new == num:
                new -= 1
            add = num-new
            for i in range(add):
                response = requests.get("http://localhost:5002/stopinstance")
                scaler.logger.debug(response.text)
        return [run, EXPAND, SHRINK, MAXMISS, MINMISS, num, new]
    return [run, EXPAND, SHRINK, MAXMISS, MINMISS]


@scaler.route('/')
# home page render
def page():

    return "Scaler is ready"


@scaler.route('/testshrink')
def testshrink():
    response = requests.get("http://localhost:5002/scalerconfig")
    result = response.json()
    run = int(result['scalerswitch'])
    EXPAND = float(result['expand'])
    SHRINK = float(result['shrink'])
    MAXMISS = float(result['maxrate'])
    MINMISS = float(result['minrate'])
    scaler.logger.debug(str(run) + ' ' + str(EXPAND) + ' ' + str(SHRINK) + ' ' + str(MAXMISS) + ' ' + str(MINMISS))
    response = requests.get("http://localhost:5002/numrunning")
    num = int(response.json())
    new = max(1, int(num*SHRINK))
    if new > 1 and new == num:
        new -= 1
    add = num-new
    for i in range(add):
        response = requests.get("http://localhost:5002/stopinstance")
        scaler.logger.debug(response.text)
    return 'OK'


@scaler.route('/testgrow')
def testgrow():
    response = requests.get("http://localhost:5002/scalerconfig")
    result = response.json()
    run = int(result['scalerswitch'])
    EXPAND = float(result['expand'])
    SHRINK = float(result['shrink'])
    MAXMISS = float(result['maxrate'])
    MINMISS = float(result['minrate'])
    scaler.logger.debug(str(run) + ' ' + str(EXPAND) + ' ' + str(SHRINK) + ' ' + str(MAXMISS) + ' ' + str(MINMISS))
    response = requests.get("http://localhost:5002/numrunning")
    num = int(response.json())
    new = max(8, int(num*EXPAND))
    if new < 8 and new == num:
        new += 1
    add = new-num
    for i in range(add):
        response = requests.get("http://localhost:5002/startinstance")
        scaler.logger.debug(response.text)
    return 'OK'
