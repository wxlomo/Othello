from flask import request
from . import scaler
import memfunc
from memfunc import getAggregateMissRate1mins
import threading
import time

missrate=0
@scaler.before_first_request
# create the thread to keep updating the statistics
def threadedUpdate():
    thread = threading.Thread(target=updatestat)
    thread.start()


# update the statistics in every 5 seconds
def updatestat():
    while True:
        time.sleep(60)
        getAggregateMissRate1mins