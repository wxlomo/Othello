"""
 * test_auto.py
 * performance testing code for the auto resizing mode
 *
 * Author: Weixuan Yang
 * Date: Nov. 11, 2022
 *
 * Help: Run the script with following arguments:
 *       - Test type: 'grow', 'shrink'
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
manager_url = "http://54.235.28.157:5002/"

key = [0, 1, 2, 3, 4, 5, 6, 7]
sns.set_theme(style="whitegrid")


def read_test():
    """Send the http request to retrieve an image with a random key

    Args:
      n/a

    Returns:
      n/a
    """
    random_key = random.choice(key)
    try:
        response = requests.post(base_url + "/api/key/" + str(random_key), verify=False)
    except Exception as error:
        print('* Error: ' + str(error))


def write_test():
    """Send the http request to retrieve an image with a random key

    Args:
      n/a

    Returns:
      n/a
    """
    random_key = random.choice(key)
    image = open('img/test.jpg', 'rb')
    data = {'key': random_key}
    files = {'file': image}
    try:
        response = requests.post(base_url + "/api/upload", files=files, data=data, verify=False)
    except Exception as error:
        print('* Error: ' + str(error))


def key_pool(mode):
    """Send the http request to upload an image with a random key

    Args:
      mode (str): shrink or grow the key pool

    Returns:
      n/a
    """
    print(str(mode) + 'ing the key pool')
    global key
    if mode == 'grow':
        key.append(randint(0, 99))
    elif mode == 'shrink':
        if len(list) > 1:
            key.pop()
    else:
        raise ValueError('No such type of test')
    print('The key pool now has: ' + str(key))


def get_miss():
    """Return the memcache miss rate

    Args:
      n/a

    Returns:
      float: the memcache miss rate
    """
    response = requests.post(manager_url + '/1minmiss', verify=False)
    print('Get miss rate: ' + str(response.json()))
    return response.json()


def get_node():
    """Return the memcache node number

    Args:
      n/a

    Returns:
      int: the memcache node number
    """
    response = requests.post(manager_url + '/numrunning', verify=False)
    print('Get node number: ' + str(response.json()))
    return response.json()


def test_auto(mode):
    """Generate the miss rate trend figure

        Args:
          mode (str): want to shrink or grow the memcache pool

        Returns:
          n/a
    """
    data = []
    current_node = 0
    while current_node == 8 or current_node == 1:
        read_test()
        write_test()
        if current_node != get_node():
            current_node = get_node()
            data.append([current_node, get_miss()])
        key_pool(mode)
    df = pd.DataFrame(data, columns=['Number of nodes', 'Miss rate'])
    fig = sns.relplot(data=df, x='Number of nodes', y='Miss rate (%)', kind='line')
    fig.fig.savefig('img/missrate_' + str(mode) + '.png')
    print('DONE.')


test_auto(str(sys.argv[1]))
