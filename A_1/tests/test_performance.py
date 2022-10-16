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
    read_number = round(request_number * read_ratio)
    write_number = request_number - read_number
    latency = 0.0
    for i in range(request_number):
        if random.random() <= read_ratio:
            latency += read_test()
        else:
            latency += write_test()
    return latency / request_number


def throughput_test(max_time, read_ratio):
    read_number = round(request_number * read_ratio)
    write_number = request_number - read_number
    i = 0
    read_i = 0
    write_i = 0
    latency = 0.0
    while i < request_number:
        if random.choice(select) == 0 and read_i < read_number:
            latency += read_test()
            read_i += 1
            i += 1
        elif random.choice(select) == 1 and write_i < write_number:
            latency += write_test()
            write_i += 1
            i += 1
    return latency / request_number



print(latency_test(10, 0.2))



