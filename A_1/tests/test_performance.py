"""
 * test_performance.py
 * performance testing code for the gallery web application
 *
 * Author: Weixuan Yang
 * Date: Oct. 11, 2022
"""

import requests
import random
import seaborn as sns
import pandas as pd
from time import time
from matplotlib import pyplot as plt
sns.set_theme(style="whitegrid")


url = "http://54.226.158.76:5000"
key = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 5]
request_numbers = list(range(1, 102, 10))
time_windows = [1.0, 2.0, 4.0, 8.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
read_ratios = [0.2, 0.5, 0.8]


def read_test():
    """Send the http request to retrieve an image with a random key

    Args:
      n/a

    Returns:
      float: the seconds of latency to handle the request
    """
    random_key = random.choice(key)
    response = requests.post(url + "/api/key/" + str(random_key), verify=False)
    if response.status_code == 500:
        raise Exception('front-end failure')
    return response.elapsed.total_seconds()


def write_test():
    """Send the http request to upload an image with a random key

    Args:
      n/a

    Returns:
      float: the seconds of latency to handle the request
    """
    random_key = random.choice(key)
    image = open('img/test.jpg', 'rb')
    data = {'key': random_key}
    files = {'file': image}
    response = requests.post(url + "/api/upload", files=files, data=data, verify=False)
    if response.status_code == 500:
        raise Exception('front-end failure')
    return response.elapsed.total_seconds()


def config(policy, capacity):
    """Send the http request to upload an image with a random key

    Args:
      policy (str): the memcache eviction policy
      capacity (int): the memcache size

    Returns:
      n/a
    """
    data = {'policy': policy, 'capacity': capacity, 'clear': 'yes'}
    response = requests.post(url + "/api/config", data=data, verify=False)
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
    total_latency = 0.0
    for test_iter in range(request_number):
        if random.random() <= read_ratio:
            total_latency += read_test()
        else:
            total_latency += write_test()
    return total_latency / request_number


def throughput_test(time_window, read_ratio):
    """Test the web application latency under certain time window

    Args:
      time_window (float): the length of time window for processing the requests
      read_ratio (int): the ratio of read requests in total requests

    Returns:
      float: the seconds of latency to handle the request
    """
    total_time = 0.0
    total_request = 0
    while total_time < time_window:
        if random.random() <= read_ratio:
            total_request += 1
            total_time += read_test()
        else:
            total_request += 1
            total_time += write_test()
    return total_request


def latency_figure(read_ratio=0.5):
    """Generate the latency trend figure for certain read_ratio

        Args:
          read_ratio (float): the ratio of read requests in total requests

        Returns:
          n/a
    """
    data = []
    config('random', 3)
    for request_number in request_numbers:
        data.append([request_number, latency_test(request_number, read_ratio), 'random'])
    config('lru', 3)
    for request_number in request_numbers:
        data.append([request_number, latency_test(request_number, read_ratio), 'lru'])
    config('lru', 0)
    for request_number in request_numbers:
        data.append([request_number, latency_test(request_number, read_ratio), 'no'])
    df = pd.DataFrame(data, columns=['Number of requests', 'Latency (seconds)', 'Policy'])
    fig = sns.relplot(data=df, x='Number of requests', y='Latency (seconds)', kind='line', style='Policy', hue='Policy')
    #[plt.annotate("{:.2f}".format(row[1]), (row[0]-0.5, row[1]+0.005)) for row in zip(df['Number of requests'], df['Latency (seconds)'])]
    fig.fig.savefig('img/latency_' + str(read_ratio) + '.png')


def throughput_figure(read_ratio=0.5):
    """Generate the latency trend figure for certain read_ratio

        Args:
          read_ratio (float): the ratio of read requests in total requests

        Returns:
          n/a
    """
    data = []
    config('random', 3)
    for time_window in time_windows:
        data.append([time_window, throughput_test(time_window, read_ratio), 'random'])
    config('lru', 3)
    for time_window in time_windows:
        data.append([time_window, throughput_test(time_window, read_ratio), 'lru'])
    config('lru', 0)
    for time_window in time_windows:
        data.append([time_window, throughput_test(time_window, read_ratio), 'no'])
    df = pd.DataFrame(data, columns=['Units of time (seconds)', 'Maximum number of requests', 'Policy'])
    fig = sns.catplot(data=df, x='Units of time (seconds)', y='Maximum number of requests', kind='bar', hue='Policy', ci=None)
    fig.fig.savefig('img/throughput_' + str(read_ratio) + '.png')


for ratio in read_ratios:
    latency_figure(ratio)
    throughput_figure(ratio)
print('DONE.')
