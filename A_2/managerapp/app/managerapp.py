"""
 * managerapp.py
 * manager app page
 *
 * Author: Haotian Chen
 * Date: Nov. 8, 2022
"""

from . import front, dbconfig
from flask import render_template, request, g, escape
from werkzeug.utils import secure_filename
import mysql.connector
import os
import requests
import base64


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





@front.route('/')
def get_home():
    """Home page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    return render_template('index.html')






@front.route('/config')
def get_config():
    """Configuration page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    

    return render_template('config.html', poli='LRU', capa="50", pool='1')



@front.route('/about')
def get_about():
    """About page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    front.logger.debug('\n* Viewing about')
    return render_template('about.html')



@front.route('/putConfig', methods=['POST'])
def put_config():
    """Commit the changes in configurations.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    
    policy = request.form['policy']
    capacity = request.form['capacity']
    front.logger.debug('\n* Configuring with capacity: ' + str(capacity) + ' and policy: ' + str(policy))
    cursor = db_wrapper('put_config', policy, capacity)
    if not cursor:
        return render_template('result.html', result='Something Wrong :(')
    if request.form['clear'] == "yes":
        response = requests.get("http://localhost:5001/clear")  # clear the cache
        front.logger.debug(response.text)
    response = requests.get("http://localhost:5001/refreshConfiguration")
    front.logger.debug(response.text)
    return render_template('result.html', result='Your Request Has Been Processed :)')

############################################################################################
@front.route('/setManual', methods=['POST'])
def set_manual():
    """Set the manual mode.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    front.logger.debug('\n* Setting manual mode')
    response = requests.get("http://localhost:5001/setManual")
    front.logger.debug(response.text)
    return render_template('result.html', result='Your Request Has Been Processed :)')

@front.route('/setAuto', methods=['POST'])
def set_auto():
    """Set the auto mode.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    front.logger.debug('\n* Setting auto mode')
    response = requests.get("http://localhost:5001/setAuto")
    front.logger.debug(response.text)
    return render_template('result.html', result='Your Request Has Been Processed :)')
############################################################################################


@front.route('/api/config', methods=['POST'])
def put_config_api():
    """The api to commit the changes in configurations.

    Args:
      n/a

    Returns:
      dict: the JSON format response of the HTTP request
    """

    policy = request.form['policy']
    capacity = request.form['capacity']
    front.logger.debug('\n* Configuring with capacity: ' + str(capacity) + ' and policy: ' + str(policy))
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
        front.logger.debug(response.text)
    response = requests.get("http://localhost:5001/refreshConfiguration")
    front.logger.debug(response.text)
    return {
        'success': 'true'
    }
