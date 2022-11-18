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
base_url = "http://3.80.40.201:5000/"
# The http address regards the manager application
manager_url = "http://3.80.40.201:5002/"

key = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
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


def read(rkey):
    """Send the http request to get an image

    Args:
      rkey (int): the key to put the image

    Returns:
      n/a
    """
    try:
        response = requests.post(base_url + "/api/key/" + str(rkey), verify=False)
    except Exception as error:
        print('* Error: ' + str(error))


def write(wkey):
    """Send the http request to put an image

    Args:
      wkey (int): the key to put the image

    Returns:
      n/a
    """
    image = open('img/test.jpg', 'rb')
    data = {'key': wkey}
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
        if len(key) < 30:
            while True:
                new_key = random.randint(1, 100)
                if new_key not in key:
                    key.append(new_key)
                    write(new_key)
                    break
    elif mode == 'shrink':
        if len(key) > 1:
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
    response = requests.get(manager_url + '/1minmiss', verify=False)
    print('Get miss rate: ' + str(response.json()))
    return response.json()


def get_node():
    """Return the memcache node number

    Args:
      n/a

    Returns:
      int: the memcache node number
    """
    response = requests.get(manager_url + '/numrunning', verify=False)
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
    for ckey in key:
        write(ckey)
        read(ckey)
    while True:
        read_test()
        read_test()
        read_test()
        read_test()
        read_test()
        current_node = get_node()
        current_miss = get_miss()
        if mode == 'grow' and current_miss < 0.75:
            key_pool('grow')
        elif mode == 'shrink' and current_miss > 0.15:
            key_pool('shrink')
        data.append([current_node, current_miss * 100])
        if current_node == 1 or current_node == 8:
            break
        sleep(5)
    df = pd.DataFrame(data, columns=['Number of nodes', 'Miss rate (%)'])
    fig = sns.relplot(data=df, x='Number of nodes', y='Miss rate (%)', kind='line')
    fig.fig.savefig('img/missrate' + str(mode) + '.png')
    print('DONE.')


test_auto(str(sys.argv[1]))
