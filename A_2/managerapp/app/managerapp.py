"""
 * managerapp.py
 * manager app page
 *
 * Author: Haotian Chen
 * Date: Nov. 8, 2022
"""


import base64
from io import BytesIO
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import mysql.connector
import requests
import memfunc
from memfunc import test2
from flask import escape, g, render_template, request
from werkzeug.utils import secure_filename

from . import dbconfig, manager


def get_db():
    """Establish the connection to the database.

    Args:
      n/a

    Returns:
      MySQLConnection: the connector to the available database.
    """
    if 'db' not in g:
        g.db = mysql.connector.connect(
            user=dbconfig.db_config['user'],
            password=dbconfig.db_config['password'],
            host=dbconfig.db_config['host'],
            database=dbconfig.db_config['database']
        )
    return g.db


def draw_charts(stats:list, y_label:str, title:str):
    """Draw the charts for the statistics.

    Args:
      stats (list): the list of statistics.

    Returns:
      n/a
    """
    # draw the charts
    x1 = [x for x in range(10)]
    print(x1, stats)
    l1 = plt.plot(x1, stats, 'r')
    plt.xlabel('Time')
    plt.ylabel(y_label)
    plt.title(title)
    sio = BytesIO()
    plt.savefig(sio, format='png')
    data = base64.encodebytes(sio.getvalue()).decode()
    src = 'data:image/png;base64,{}'.format(data)
    plt.close()
    return src
    

@manager.route('/')
def get_home():
    """Home page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    y_label = ['missRate', 'hitRate', 'numberItems', 'currentSize', 'totalRequests']
    title = ['missRate', 'hitRate', 'numberItems', 'currentSize', 'totalRequests']
    stats = test1()
  
    for i in range(len(stats)):
        
        test2=(draw_charts(stats[i], y_label[i], title[i]))
        
    return render_template('index.html', src=test2)






@manager.route('/config')
def get_config():
    """Configuration page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    

    return render_template('config.html', poli='LRU', capa="50", pool='1',minrate='15', maxrate='75', expand='1', shrink='1')



@manager.route('/about')
def get_about():
    """About page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    manager.logger.debug('\n* Viewing about')
    return render_template('about.html')



@manager.route('/putConfig', methods=['POST'])
def put_config():
    """Commit the changes in configurations.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    
    policy = request.form['policy']
    capacity = request.form['capacity']
    manager.logger.debug('\n* Configuring with capacity: ' + str(capacity) + ' and policy: ' + str(policy))
    cursor = db_wrapper('put_config', policy, capacity)
    if not cursor:
        return render_template('result.html', result='Something Wrong :(')
    if request.form['clear'] == "yes":
        response = requests.get("http://localhost:5001/clear")  # clear the cache
        manager.logger.debug(response.text)
    response = requests.get("http://localhost:5001/refreshConfiguration")
    manager.logger.debug(response.text)
    return render_template('result.html', result='Your Request Has Been Processed :)')

############################################################################################
@manager.route('/setManual', methods=['POST'])
def set_manual():
    """Set the manual mode.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    manager.logger.debug('\n* Setting manual mode')
    response = requests.get("http://localhost:5001/setManual")
    manager.logger.debug(response.text)
    return render_template('result.html', result='Your Request Has Been Processed :)')

@manager.route('/setAuto', methods=['POST'])
def set_auto():
    """Set the auto mode.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    manager.logger.debug('\n* Setting auto mode')
    response = requests.get("http://localhost:5001/setAuto")
    manager.logger.debug(response.text)
    return render_template('result.html', result='Your Request Has Been Processed :)')
  
@manager.route('/deleteData', methods=['POST'])
def delete_data():
    """Delete the data.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    manager.logger.debug('\n* Deleting data')
    response = requests.get("http://localhost:5001/deleteData")
    manager.logger.debug(response.text)
    return render_template('result.html', result='Your Request Has Been Processed :)')
  
@manager.route('/clearMemcache', methods=['POST'])
def clear_memcache():
    """Clear the memcache.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    manager.logger.debug('\n* Clearing memcache')
    response = requests.get("http://localhost:5001/clear")
    manager.logger.debug(response.text)
    return render_template('result.html', result='Your Request Has Been Processed :)')
############################################################################################


@manager.route('/api/config', methods=['POST'])
def put_config_api():
    """The api to commit the changes in configurations.

    Args:
      n/a

    Returns:
      dict: the JSON format response of the HTTP request
    """

    policy = request.form['policy']
    capacity = request.form['capacity']
    manager.logger.debug('\n* Configuring with capacity: ' + str(capacity) + ' and policy: ' + str(policy))
    cursor = db_wrapper('put_config', policy, capacity)
    if not cursor:
        return {
            'success': 'false',
            'error': {
                'code': 500,
                'message': 'Internal Server Error: Fail in connecting to database'
            }
        }
    if request.form['clear'] == "yes":  # clear the cache
        response = requests.get("http://localhost:5001/clear")
        manager.logger.debug(response.text)
    response = requests.get("http://localhost:5001/refreshConfiguration")
    manager.logger.debug(response.text)
    return {
        'success': 'true'
    }
