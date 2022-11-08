"""
 * test_performance.py
 * performance testing code for the gallery web application
 *
 * Author: Weixuan Yang
 * Date: Oct. 11, 2022
 *
 * Help: Rename the image that is used for testing as 'test.jpg' and
 * place it into the /img folder then set the base_url variable to the
 * http address regards the deployed web application. Run the test,
 * the result will be generated as figures in /img folder.
"""


import requests
import random
import seaborn as sns
import pandas as pd
from time import time, sleep
from matplotlib import pyplot as plt
from concurrent.futures import ThreadPoolExecutor, as_completed


# The http address regards the deployed web application
base_url = "http://54.235.28.157:5000/"

key = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
capa = 3
request_numbers = list(range(1, 52, 5))
time_windows = [0.2, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 20.0, 30.0]
sns.set_theme(style="whitegrid")


def gen_read_url(n):
    """Generate read urls for parallel executor

    Args:
      n (int): the number of url needed

    Returns:
      list: the list of the urls
    """
    read_url = []
    for iter in range(n):
        read_url.append(base_url + "/api/key/")
    return read_url


def gen_write_url(n):
    """Generate write urls for parallel executor

    Args:
      n (int): the number of url needed

    Returns:
      list: the list of the urls
    """
    write_url = []
    for iter in range(n):
        write_url.append(base_url + "/api/upload")
    return write_url


def read_test_latency(read_url):
    """Send the http request to retrieve an image with a random key

    Args:
      read_url (str): the url that needs to be executed

    Returns:
      float: the seconds of latency to handle the request
    """
    random_key = random.choice(key)
    try:
        response = requests.post(read_url + str(random_key), verify=False)
        return response.elapsed.total_seconds()
    except Exception:
        return 10.0


def write_test_latency(write_url):
    """Send the http request to upload an image with a random key

    Args:
      write_url (str): the url that needs to be executed

    Returns:
      float: the seconds of latency to handle the request
    """
    random_key = random.choice(key)
    image = open('img/test.jpg', 'rb')
    data = {'key': random_key}
    files = {'file': image}
    try:
        response = requests.post(write_url, files=files, data=data, verify=False)
        return response.elapsed.total_seconds()
    except Exception:
        return 10.0


def read_test_runtime(read_url):
    """Send the http request to retrieve an image with a random key

    Args:
      read_url (str): the url that needs to be executed

    Returns:
      int: one request has been executed
    """
    random_key = random.choice(key)
    try:
        response = requests.post(read_url + str(random_key), verify=False)
        return 1
    except Exception:
        return 0


def write_test_runtime(write_url):
    """Send the http request to upload an image with a random key

    Args:
      write_url (str): the url that needs to be executed

    Returns:
      int: one request has been executed
    """
    random_key = random.choice(key)
    image = open('img/test.jpg', 'rb')
    data = {'key': random_key}
    files = {'file': image}
    try:
        response = requests.post(write_url, files=files, data=data, verify=False)
        return 1
    except Exception:
        return 0


def config(policy, capacity):
    """Send the http request to upload an image with a random key

    Args:
      policy (str): the memcache eviction policy
      capacity (int): the memcache size

    Returns:
      n/a
    """
    print('Switch configurations to ' + str(policy) + ' and with ' + str(capacity) + 'MB capacity')
    data = {'policy': policy, 'capacity': capacity, 'clear': 'yes'}
    response = requests.post(base_url + "/api/config", data=data, verify=False)
    if response.status_code == 500:
        raise Exception('front-end failure')


def latency_test(request_number, read_ratio):
    """Test the web application latency under certain request numbers

    Args:
      request_number (int): total number of requests that will be processed
      read_ratio (int): the ratio of read requests in total requests

    Returns:
      float: the seconds of latency to handle the request
    """
    print('Testing latency for ' + str(request_number) + ' requests and ' + str(read_ratio) + ' read ratio')
    read_number = round(request_number * read_ratio)
    write_number = request_number - read_number
    read_url = gen_read_url(read_number)
    write_url = gen_write_url(write_number)
    total_latency = 0.0
    futures = []
    with ThreadPoolExecutor(max_workers=request_number) as executor:
        futures += {executor.submit(read_test_latency, url): url for url in read_url}
        futures += {executor.submit(write_test_latency, url): url for url in write_url}
        for future in as_completed(futures):
            total_latency += future.result()
    return total_latency / request_number


def throughput_test(time_window, read_ratio):
    """Test the web application latency under certain time window

    Args:
      time_window (float): the length of time window for processing the requests
      read_ratio (int): the ratio of read requests in total requests

    Returns:
      int: the number of requests that have been processed
    """
    print('Testing throughput within ' + str(time_window) + ' seconds and ' + str(read_ratio) + ' read ratio')
    total_request = 0
    time_window += time()
    while time() < time_window:
        read_number = round(10 * read_ratio)
        write_number = 10 - read_number
        read_url = gen_read_url(read_number)
        write_url = gen_write_url(write_number)
        futures = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures += {executor.submit(read_test_runtime, url): url for url in read_url}
            futures += {executor.submit(write_test_runtime, url): url for url in write_url}
            for future in as_completed(futures):
                if time() > time_window:
                    executor.shutdown()
                    return total_request
                total_request += future.result()
    return total_request


def latency_figure(read_ratio):
    """Generate the latency trend figure for certain read_ratio

        Args:
          read_ratio (float): the ratio of read requests in total requests

        Returns:
          n/a
    """
    data = []
    config('random', capa)
    for request_number in request_numbers:
        data.append([request_number, latency_test(request_number, read_ratio), 'random'])
    sleep(5)
    config('lru', capa)
    for request_number in request_numbers:
        data.append([request_number, latency_test(request_number, read_ratio), 'lru'])
    sleep(5)
    config('lru', 0)
    for request_number in request_numbers:
        data.append([request_number, latency_test(request_number, read_ratio), 'no'])
    sleep(5)
    df = pd.DataFrame(data, columns=['Number of requests', 'Latency (seconds)', 'Policy'])
    fig = sns.relplot(data=df, x='Number of requests', y='Latency (seconds)', kind='line', style='Policy', hue='Policy')
    fig.fig.savefig('img/latency_' + str(read_ratio) + '.png')


def throughput_figure(read_ratio):
    """Generate the latency trend figure for certain read_ratio

        Args:
          read_ratio (float): the ratio of read requests in total requests

        Returns:
          n/a
    """
    data = []
    config('random', capa)
    for time_window in time_windows:
        data.append([time_window, throughput_test(time_window, read_ratio), 'random'])
    sleep(5)
    config('lru', capa)
    for time_window in time_windows:
        data.append([time_window, throughput_test(time_window, read_ratio), 'lru'])
    sleep(5)
    config('lru', 0)
    for time_window in time_windows:
        data.append([time_window, throughput_test(time_window, read_ratio), 'no'])
    sleep(5)
    df = pd.DataFrame(data, columns=['Units of time (seconds)', 'Maximum number of requests', 'Policy'])
    fig = sns.catplot(data=df, x='Units of time (seconds)', y='Maximum number of requests', kind='bar', hue='Policy', ci=None)
    fig.fig.savefig('img/throughput_' + str(read_ratio) + '.png')


def test_performance(type, ratio=0.5):
    """Run the performance test

        Args:
            type (str): the test of the performance ('latency', 'throughput')
            ratio (float, optional): the read request ratio to the total requests

        Returns:
            n/a
    """
    if type == 'latency':
        latency_figure(ratio)
    elif type == 'throughput':
        throughput_figure(ratio)
    else:
        raise ValueError('No such type of test')
    print('DONE.')

# Separated testings are suggested to avoid timeout,
# such as: test_performance('latency', 0.5)
for rratio in [0.2, 0.5, 0.8]:
    test_performance('latency', rratio)
    test_performance('throughput', rratio)
