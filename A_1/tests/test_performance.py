"""
 * test_performance.py
 * performance testing code for the gallery web application
 *
 * Author: Weixuan Yang
 * Date: Oct. 11, 2022
"""

import requests
import random
from time import time
from matplotlib import pyplot as plt
import seaborn as sns


url = "http://54.226.158.76:5000/"
key = list(range(0, 10))


def read_test():
    random_key = random.choice(key)
    response = requests.post(url + "api/key/" + str(random_key))
    if response.status_code == 500:
        raise Exception('front-end failure')
    return response.elapsed.total_seconds()


def write_test():
    random_key = random.choice(key)
    image = open('test.jpg', 'rb')
    data = {'key': random_key}
    files = {'file': image}
    response = requests.post(url + "api/upload", files=files, data=data)
    if response.status_code == 500:
        raise Exception('front-end failure')
    return response.elapsed.total_seconds()


def latency_test(request_number, read_ratio):
    total_latency = 0.0
    for i in range(request_number):
        if random.random() <= read_ratio:
            total_latency += read_test()
        else:
            total_latency += write_test()
    return total_latency / request_number


def throughput_test(max_time, read_ratio):
    total_latency = 0.0
    total_request = 0
    while total_latency < max_time:
        if random.random() <= read_ratio:
            total_request += 1
            total_latency += read_test()
        else:
            total_request += 1
            total_latency += write_test()
    return request_number



print(latency_test(10, 0.2))



