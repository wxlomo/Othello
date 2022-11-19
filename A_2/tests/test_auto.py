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
from matplotlib.ticker import MultipleLocator


# The http address regards the deployed web application
base_url = "http://52.54.105.207:5000/"
# The http address regards the manager application
manager_url = "http://52.54.105.207:5002/"

key = []
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
        while True:
            new_key = random.randint(1, 10000)
            if new_key not in key:
                key.append(new_key)
                write(new_key)
                break
    elif mode == 'shrink':
        if len(key) > 1:
            key.pop()
    else:
        raise ValueError('No such type of test')
    print('The key pool now has ' + str(len(key)) + ' keys')


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
    data2 = []
    previous_miss = 0.0
    previous_key = 0
    if mode == 'grow':
        previous_node = 1
        for i in range(4):
            key_pool('grow')
    else:
        previous_node = 8
        for i in range(150):
            key_pool('grow')
    while True:
        read_test()
        read_test()
        read_test()
        read_test()
        read_test()
        current_node = get_node()
        current_miss = get_miss()
        if mode == 'grow' and current_miss <= 0.75:
            key_pool('grow')
        elif mode == 'shrink' and current_miss >= 0.15:
            key_pool('shrink')
        current_key = len(key)
        if current_node == previous_node and current_miss != previous_miss and current_key == previous_key:
            if mode == 'grow':
                current_key += 1
            else:
                current_key -= 1
        if current_node != previous_node:
            if current_node == 1 or current_node == 2 or current_node == 4 or current_node == 8:
                data2.append([current_node, current_miss * 100])
        if current_node != previous_node or current_miss != previous_miss:
            previous_node = current_node
            previous_miss = current_miss
            previous_key = current_key
            if current_node == 1 or current_node == 2 or current_node == 4 or current_node == 8:
                data.append([current_key, current_node, current_miss * 100])
        if mode == 'grow' and current_node == 8 and current_miss <= 0.75:
            break
        if mode == 'shrink' and current_node == 1 and current_miss >= 0.15:
            break
        if current_key == 200 or current_key == 1:
            break
        sleep(5)
    df = pd.DataFrame(data, columns=['Number of keys', 'Number of nodes', 'Miss rate (%)'])
    df2 = pd.DataFrame(data2, columns=['Number of nodes after scale', 'Miss rate (%)'])
    df.to_csv('img/auto-scalar-' + str(mode) + '.csv', encoding='utf-8')
    df2.to_csv('img/auto-scalar-resize-' + str(mode) + '.csv', encoding='utf-8')
    fig = sns.relplot(data=df, x='Number of keys', y='Miss rate (%)', kind='line', hue='Number of nodes', palette=sns.color_palette("tab10"), sort=False)
    fig.axes[0][0].yaxis.set_major_locator(MultipleLocator(5))
    sns.move_legend(fig, 'upper right', bbox_to_anchor=(.8, 1))
    if mode == 'shrink':
        for ax in fig.axes[0]:
            ax.invert_xaxis()
    fig.fig.savefig('img/auto-scalar-' + str(mode) + '.png')
    fig2 = sns.relplot(data=df2, x='Number of nodes after scale', y='Miss rate (%)', kind='line', sort=False)
    if mode == 'grow':
        fig2.set(ylim=(70, 100))
    else:
        fig2.set(ylim=(0, 20))
        for ax in fig2.axes[0]:
            ax.invert_xaxis()
    fig2.fig.savefig('img/auto-scalar-resize-' + str(mode) + '.png')
    print('DONE.')


test_auto(str(sys.argv[1]))
