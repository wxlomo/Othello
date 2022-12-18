"""
 * test_manual.py
 * performance testing code for the manual resizing mode
 *
 * Author: Weixuan Yang
 * Date: Nov. 11, 2022
 *
 * Help: Run the script with following arguments:
 *       - Mode: 'constant', 'shrink', 'grow'
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
from config import base_url, manager_url


key = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]
request_numbers = [1, 10, 20, 30, 40, 50, 60, 70]
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
    except Exception as error:
        print('* Error ' + str(error))
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
    except Exception as error:
        print('* Error ' + str(error))
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
    except Exception as error:
        print('* Error ' + str(error))
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
    except Exception as error:
        print('* Error ' + str(error))
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
                response = requests.get(manager_url + "/stopinstance", verify=False)
                if response.status_code == 500:
                    raise Exception('front-end failure')
        elif mode == 'grow':
            for it in range(time):
                response = requests.get(manager_url + "/startinstance", verify=False)
                if response.status_code == 500:
                    raise Exception('front-end failure')
        else:
            raise ValueError('No such mode')
    except Exception as error:
        print('* Error: ' + str(error))


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


def latency_figure(mode, read_ratio=0.5):
    """Generate the latency trend figure for certain read_ratio

        Args:
          mode (str): the mode of the test (shrink, grow, constant)
          read_ratio (float, optional): the ratio of read requests in total requests

        Returns:
          n/a
    """
    data = []
    config_pool('shrink', 8)
    if mode == 'shrink':
        config_pool('grow', 8)
    elif mode == 'constant':
        config_pool('grow', 4)
    elif mode == 'grow':
        config_pool('grow', 1)
    for request_number in request_numbers:
        sleep(2)
        data.append([request_number, latency_test(request_number, read_ratio)])
        if mode == 'shrink' or mode == 'grow':
            config_pool(mode, 1)
    df = pd.DataFrame(data, columns=['Number of requests', 'Latency (seconds)'])
    df.to_csv('img/manual-latency' + str(mode) + '.csv', encoding='utf-8')
    fig = sns.relplot(data=df, x='Number of requests', y='Latency (seconds)', kind='line', hue=None)
    fig.fig.savefig('img/manual-latency-' + str(mode) + '.png')


def throughput_figure(mode, read_ratio=0.5):
    """Generate the latency trend figure for certain read_ratio

        Args:
          mode (str): the mode of the test (shrink, grow, constant)
          read_ratio (float, optional): the ratio of read requests in total requests

        Returns:
          n/a
    """
    data = []
    config_pool('shrink', 8)
    if mode == 'shrink':
        config_pool('grow', 8)
    elif mode == 'constant':
        config_pool('grow', 4)
    elif mode == 'grow':
        config_pool('grow', 1)
    for time_window in time_windows:
        sleep(2)
        data.append([time_window, throughput_test(time_window, read_ratio)])
        if mode == 'shrink' or mode == 'grow':
            config_pool(mode, 1)
    df = pd.DataFrame(data, columns=['Units of time (seconds)', 'Maximum number of requests'])
    df.to_csv('img/manual-throughput' + str(mode) + '.csv', encoding='utf-8')
    fig = sns.catplot(data=df, x='Units of time (seconds)', y='Maximum number of requests', kind='bar', hue=None, ci=None)
    fig.fig.savefig('img/manual-throughput-' + str(mode) + '.png')


def test_manual(mode):
    """Run the performance test

        Args:
            mode (str): the mode of the test (shrink, grow, constant)

        Returns:
            n/a
    """
    print('Executing test for ' + str(mode) + ' Memcache nodes')
    latency_figure(mode)
    throughput_figure(mode)
    print('DONE.')


test_manual(str(sys.argv[1]))
