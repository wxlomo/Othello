"""
 * test_manual.py
 * performance testing code
 *
 * Author: Weixuan Yang
 * Date: December. 17, 2022
 *
 * The result will be generated as figures in current folder.
"""
import requests
import seaborn as sns
import pandas as pd
from time import time, sleep
from concurrent.futures import ThreadPoolExecutor, as_completed
from random import choice
from config import base_url
from uuid import uuid4
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


request_numbers = [1, 10, 20, 30, 40, 50, 60, 70, 80]
time_windows = [0.2, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0]
sns.set_theme(style="whitegrid")


def create_test_latency():
    """Send the http request to create a game

    Args:
      n/a

    Returns:
      float: the seconds of latency to handle the request
    """
    try:
        response = requests.post(base_url + str('api/create_game'), verify=False, data={'player_name': uuid4(), 'player_side': 'Dark'})
        return response.elapsed.total_seconds()
    except Exception as error:
        print('* Error ' + str(error))
        return 10.0


def join_test_latency():
    """Send the http request to get all the available games and join one of them

    Args:
      n/a

    Returns:
      float: the seconds of latency to handle the request
    """
    total_elapsed_seconds = 0.0
    game_id = uuid4()
    try:
        response = requests.post(base_url + 'api/join_game', data={'player_name': uuid4(), 'game_id': game_id}, verify=False)
        total_elapsed_seconds += response.elapsed.total_seconds()
        return total_elapsed_seconds
    except Exception as error:
        print('* Error ' + str(error))
        return 10.0


def create_test_runtime():
    """Send the http request to create a game

    Args:
      n/a

    Returns:
      int: 1 if success, 0 if fail
    """
    try:
        response = requests.post(base_url + str('api/create_game/'), verify=False, data={'player_name': uuid4(), 'tile': 'Dark'})
        print(response.json())
        return response.elapsed.total_seconds()
    except Exception as error:
        print('* Error ' + str(error))
        return 10.0


def join_test_runtime():
    """Send the http request to get all the available games and join one of them

    Args:
      n/a

    Returns:
      int: 1 if success, 0 if fail
    """
    try:
        response = requests.post(base_url + 'api/join/', verify=False)
    except Exception as error:
        print('* Error ' + str(error))
        return 0
    game_id = choice(response.json()['games'])
    try:
        response = requests.post(base_url + 'api/join_game/', data={'player_name': uuid4(), 'game_id': game_id}, verify=False)
        return 1
    except Exception as error:
        print('* Error ' + str(error))
        return 0


def latency_test(request_number, mode):
    """Test the web application latency under certain request numbers

    Args:
      request_number (int): total number of requests that will be processed
      mode (str): create or join the game

    Returns:
      float: the seconds of latency to handle the request
    """
    print('Testing latency for ' + str(request_number) + ' requests')
    total_latency = 0.0
    total_thread = [i for i in range(request_number)]
    futures = []
    if mode == 'create':
        with ThreadPoolExecutor(max_workers=request_number) as executor:
            futures += {executor.submit(create_test_latency): i for i in total_thread}
            for future in as_completed(futures):
                total_latency += future.result()
    elif mode == 'join':
        with ThreadPoolExecutor(max_workers=request_number) as executor:
            futures += {executor.submit(join_test_latency): i for i in total_thread}
            for future in as_completed(futures):
                total_latency += future.result()
    return total_latency / request_number


def throughput_test(time_window, mode):
    """Test the web application latency under certain time window

    Args:
      time_window (float): the length of time window for processing the requests
      mode (str): create or join the game

    Returns:
      int: the number of requests that have been processed
    """
    print('Testing throughput within ' + str(time_window) + ' seconds')
    total_request = 0
    total_thread = [i for i in range(10)]
    time_window += time()
    if mode == 'create':
        while time() < time_window:
            futures = []
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures += {executor.submit(create_test_latency): i for i in total_thread}
                for future in as_completed(futures):
                    if time() > time_window:
                        executor.shutdown()
                        return total_request
                    total_request += future.result()
    elif mode == 'join':
        while time() < time_window:
            futures = []
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures += {executor.submit(join_test_latency): i for i in total_thread}
                for future in as_completed(futures):
                    if time() > time_window:
                        executor.shutdown()
                        return total_request
                    total_request += future.result()
    return total_request


def latency_figure():
    """Generate the latency trend figure for certain read_ratio

        Args:
          n/a

        Returns:
          n/a
    """
    data = []
    for request_number in request_numbers:
        sleep(2)
        data.append([request_number, latency_test(request_number, 'create'), 'Create'])
    for request_number in request_numbers:
        sleep(2)
        data.append([request_number, latency_test(request_number, 'join'), 'Join'])
    df = pd.DataFrame(data, columns=['Number of requests', 'Latency (seconds)', 'Mode'])
    df.to_csv('latency.csv', encoding='utf-8')
    fig = sns.relplot(data=df, x='Number of requests', y='Latency (seconds)', kind='line', style='Mode', hue='Mode')
    fig.fig.savefig('latency.png')


def throughput_figure():
    """Generate the latency trend figure for certain read_ratio

        Args:
          n/a

        Returns:
          n/a
    """
    data = []
    for time_window in time_windows:
        sleep(2)
        data.append([time_window, throughput_test(time_window, 'create'), 'Create'])
    for time_window in time_windows:
        sleep(2)
        data.append([time_window, throughput_test(time_window, 'join'), 'Join'])
    df = pd.DataFrame(data, columns=['Units of time (seconds)', 'Maximum number of requests', 'Mode'])
    df.to_csv('latency.csv', encoding='utf-8')
    fig = sns.catplot(data=df, x='Units of time (seconds)', y='Maximum number of requests', kind='bar', hue='Mode', ci=None)
    fig.fig.savefig('throughput.png')


def test():
    latency_figure()
    throughput_figure()


test()
