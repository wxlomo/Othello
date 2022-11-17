"""
 * test_manual.py
 * performance testing code for the manual resizing mode
 *
 * Author: Weixuan Yang
 * Date: Nov. 11, 2022
 *
 * Help: Run the script with following arguments:
 *       - Test type: 'latency', 'throughput'
 *       - Starting pool size: integer between 1 and 8
 *       - Ending pool size: integer between 1 and 8
 * Rename the image that is used for testing as 'test.jpg' and
 * place it into the /img folder then set the base_url variable to the
 * http address regards the deployed web application. Run the test,
 * the result will be generated as figures in /img folder.
"""
import sys

import requests
import random
import seaborn as sns
import pandas as pd
from time import time, sleep
from matplotlib import pyplot as plt
from concurrent.futures import ThreadPoolExecutor, as_completed


# The http address regards the deployed web application
base_url = "http://54.235.28.157:5000/"
# The http address regards the manager application
manager_url = "http://54.235.28.157:5000/"

key = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
request_numbers = list(range(1, 52, 10))
time_windows = [0.2, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0]
sns.set_theme(style="whitegrid")


def gen_read_url(n):
    """Generate read urls for parallel executor

    Args:
      n (int): the number of url needed

    Returns:
      list: the list of the urls
    """
    read_url = []
    for it in range(n):
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
    for it in range(n):
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


def config_pool(mode, time=1):
    """Send the http request to upload an image with a random key

    Args:
      mode (str): shrink or grow the memcache pool
      time (int): the time of the execution

    Returns:
      n/a
    """
    print(str(mode) + 'ing the memcache pool by ' + str(time))
    try:
        if mode == 'shrink':
            for it in range(time):
                response = requests.post(manager_url + "/stopinstance", verify=False)
        elif mode == 'grow':
            for it in range(time):
                response = requests.post(manager_url + "/startinstance", verify=False)
        else:
            raise ValueError('No such mode')
    except Exception as error:
        print('* Error: ' + str(error))
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


def latency_figure(start_pool_size, end_pool_size, read_ratio=0.5):
    """Generate the latency trend figure for certain read_ratio

        Args:
          start_pool_size (int): the starting memcache pool size
          end_pool_size (int): the ending memcache pool size
          read_ratio (float, optional): the ratio of read requests in total requests

        Returns:
          n/a
    """
    data = []
    config_pool('grow', start_pool_size)
    current_pool_size = start_pool_size
    for request_number in request_numbers:
        data.append([request_number, latency_test(request_number, read_ratio), current_pool_size])
    if start_pool_size > end_pool_size:
        while current_pool_size >= end_pool_size:
            sleep(5)
            current_pool_size -= 1
            config_pool('shrink', start_pool_size)
            for request_number in request_numbers:
                data.append([request_number, latency_test(request_number, read_ratio), current_pool_size])
    elif start_pool_size < end_pool_size:
        while current_pool_size <= end_pool_size:
            sleep(5)
            current_pool_size += 1
            config_pool('grow', start_pool_size)
            for request_number in request_numbers:
                data.append([request_number, latency_test(request_number, read_ratio), current_pool_size])
    df = pd.DataFrame(data, columns=['Number of requests', 'Latency (seconds)', 'Memcache pool size'])
    fig = sns.relplot(data=df, x='Number of requests', y='Latency (seconds)', kind='line', style='Memcache pool size', hue='Memcache pool size')
    fig.fig.savefig('img/latency_' + str(read_ratio) + '.png')


def throughput_figure(start_pool_size, end_pool_size, read_ratio=0.5):
    """Generate the latency trend figure for certain read_ratio

        Args:
          start_pool_size (int): the starting memcache pool size
          end_pool_size (int): the ending memcache pool size
          read_ratio (float, optional): the ratio of read requests in total requests

        Returns:
          n/a
    """
    data = []
    config_pool('grow', start_pool_size)
    current_pool_size = start_pool_size
    for time_window in time_windows:
        data.append([time_window, throughput_test(time_window, read_ratio), current_pool_size])
    if start_pool_size > end_pool_size:
        while current_pool_size >= end_pool_size:
            sleep(5)
            current_pool_size -= 1
            config_pool('shrink', start_pool_size)
            for time_window in time_windows:
                data.append([time_window, throughput_test(time_window, read_ratio), current_pool_size])
    elif start_pool_size < end_pool_size:
        while current_pool_size <= end_pool_size:
            sleep(5)
            current_pool_size += 1
            config_pool('grow', start_pool_size)
            for time_window in time_windows:
                data.append([time_window, throughput_test(time_window, read_ratio), current_pool_size])
    df = pd.DataFrame(data, columns=['Units of time (seconds)', 'Maximum number of requests', 'Memcache pool size'])
    fig = sns.catplot(data=df, x='Units of time (seconds)', y='Maximum number of requests', kind='bar', hue='Memcache pool size',ci=None)
    fig.fig.savefig('img/throughput_' + str(read_ratio) + '.png')


def test_manual(type, start_pool_size, end_pool_size):
    """Run the performance test

        Args:
            type (str): the test of the performance ('latency', 'throughput')
            start_pool_size (int): the starting memcache pool size
            end_pool_size (int): the ending memcache pool size

        Returns:
            n/a
    """
    if type == 'latency':
        latency_figure(start_pool_size, end_pool_size)
    elif type == 'throughput':
        throughput_figure(start_pool_size, end_pool_size)
    else:
        raise ValueError('No such type of test')
    print('DONE.')


test_manual(str(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
