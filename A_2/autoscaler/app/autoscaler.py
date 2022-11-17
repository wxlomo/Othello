from flask import request
from . import scaler
import time
import requests  
import threading

t = 0


@scaler.before_first_request
def threadedUpdate():
    global t
    t = 1
    thread1 = threading.Thread(target=auto)
    thread1.start()


# update every 1 mins
def auto():
    while True: 
        time.sleep(60)
        stat()
    

@scaler.route('/autonow')
def stat():
    global t
    t = 4
    response = requests.get("http://localhost:5002/scalerconfig")
    result = response.json()
    run = int(result['scalerswitch'])
    
    EXPAND = float(result['expand'])
    
    SHRINK = float(result['shrink'])
    
    MAXMISS = float(result['maxrate'])
    
    MINMISS = float(result['minrate'])
    if run:
        response = requests.get("http://localhost:5002/1minmiss")
        missrate = float(response.json())
        response = requests.get("http://localhost:5002/numrunning")
        num = int(response.json())
        new = num
        if missrate > MAXMISS:
            new = min(8, int(num*EXPAND))
            if new < 8 and new == num:
                new += 1
            add = new-num
            for i in range(add):
                response = requests.get("http://localhost:5002/startinstance")
                scaler.logger.debug(response.text)
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
# status page render
def page():
    global t
    return str(t)


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
