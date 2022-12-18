"""
 * test_func.py
 * performance testing code for the gallery web application
 *
 * Author: Weixuan Yang
 * Date: Oct. 11, 2022
 *
 * Help: Rename the image that is used for testing as 'test.jpg' and
 * place it into the /img folder then set the base_url variable to the
 * http address regards the deployed web application. Run the test with
 * an iteration number, such as "python test_func.py 5"
"""


import requests
import sys


# The http address regards the deployed web application
base_url = "http://3.80.40.201:5000"


def read_all_test():
    """Send the http request to retrieve all keys

    Args:
      n/a

    Returns:
      list: the list of all the keys
    """
    response = requests.post(base_url + "/api/list_keys")
    if response.json()['success'] != 'true':
        raise Exception('Error: ') + str(response.json()['error'])
    else:
        print('Read all keys success')
        return response.json()['keys']


def read_test(key):
    """Send the http request to retrieve an image with a random key

    Args:
      key (str): the key of the image

    Returns:
      str: the image
    """
    response = requests.post(base_url + "/api/key/" + str(key))
    if response.json()['success'] != 'true':
        raise Exception('Error: ') + str(response.json()['error'])
    else:
        print('Read key ' + str(key) + ' success')
        return response.json()['content']


def write_test(key):
    """Send the http request to upload an image with a key

    Args:
      key (str): the key of the image

    Returns:
      n/a
    """
    image = open('img/test.jpg', 'rb')
    data = {'key': key}
    files = {'file': image}
    response = requests.post(base_url + "/api/upload", files=files, data=data)
    if response.json()['success'] != 'true':
        raise Exception('Error: ' + str(response.json()['error']))
    else:
        print('Upload with key ' + str(key) + ' success')


def fun_test(iter):
    """Test the functionality of the application

        Args:
          iter (int): the iteration for running the test

        Returns:
          n/a
    """
    for i in range(iter):
        write_test(i)
        keys = read_all_test()
        if not keys:
            raise Exception('Error: fail to read the key')
        for key in keys:
            image = read_test(key)
            if not image:
                raise Exception('Error: fail to read the image')
        print('Test for keys from 0 to ' + str(i) + ' success')
    print('DONE.')


fun_test(int(sys.argv[1]))
