"""
 * managerapp.py
 * manager app page
 *
 * Author: Haotian Chen
 * Date: Nov. 8, 2022
"""
import base64
import os
from io import BytesIO
import traceback
import json
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import ticker
import mysql.connector
import requests
from flask import escape, g, jsonify, render_template, request
from werkzeug.utils import secure_filename
from . import manager, managerfunc
matplotlib.use('Agg')


# variables
policy = 'lru'
capacity = 4
minrate = '15'
maxrate = '75'
expand = '1.0'
shrink = '1.0'
scalerswitch = '0'


def draw_charts(stats: list, y_label: str, title: str):
    """Draw the charts for the statistics.

    Args:
      stats (list): the list of statistics.
      y_label (str): the label of-y axis
      title (str): the title of the figure

    Returns:
      encoded_img (str): the encoded image of the chart.
    """
    # draw the charts
    x1 = [x for x in range(len(stats))]
    l1 = plt.plot(x1, stats, 'r')
    plt.xlabel('Time')
    plt.ylabel(y_label)
    plt.title(title)
    sio = BytesIO()
    plt.savefig(sio, format='png')
    data = base64.encodebytes(sio.getvalue()).decode()  # base64encode
    src = 'data:image/png;base64,{}'.format(data)
    plt.close()
    return src


def draw_charts_percentage(stats: list, y_label: str, title: str):
    """Draw the charts for the statistics.

    Args:
      stats (list): the list of statistics.
      y_label (str): the label of y-axis
      title (str): the title of the figure

    Returns:
      encoded_img (str): the encoded image of the chart.
    """
    # draw the charts
    x1 = [x for x in range(len(stats))]
    l1 = plt.plot(x1, stats, 'r')   
    plt.gca().yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=1))
    plt.xlabel('Time')
    plt.ylabel(y_label)
    plt.title(title)
    sio = BytesIO()
    plt.savefig(sio, format='png')
    data = base64.encodebytes(sio.getvalue()).decode()  # base64encode
    src = 'data:image/png;base64,{}'.format(data)
    plt.close()
    return src 


@manager.before_first_request
def before_first_request():
    managerfunc.init_ec2_instances()
    response = requests.get("http://localhost:5003/")
    

@manager.route('/')
def get_home():
    """Home page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    y_label = ['numberItems', 'currentSize', 'totalRequests', 'missRate', 'hitRate']
    title = ['numberItems', 'currentSize', 'totalRequests', 'missRate', 'hitRate']
    result = []
    # stat1 = [x for x in range(30)]
    # stat2 = [2*x for x in range(50)]
    # stat3 = [3*x for x in range(30)]
    # stat4 = [x*0.01 for x in range(30)]
    # stat5 = [5*x for x in range(30)]
    # stats = [stat1, stat2, stat3, stat4, stat5]
    # num=0
    stats = managerfunc.getAggregateStat30Mins()
    manager.logger.debug(stats)
    num = managerfunc.num_running()
    for i in [0, 1, 2]:
        result.append((draw_charts(stats[i], y_label[i], title[i])))
    for i in [3, 4]:
        result.append((draw_charts_percentage(stats[i], y_label[i], title[i])))
        
    return render_template('index.html', numofinstance=num, src1=result[0], src2=result[1], src3=result[2], src4=result[3], src5=result[4])


# render config page
@manager.route('/config')
def get_config():
    """Configuration page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    pool = managerfunc.num_running()
    # pool = 5
    if scalerswitch == '0':
        sswitch = 'Off'
    else:
        sswitch = 'On'
      
    return render_template('config.html', switch=sswitch, poli=policy, capa=capacity, pool=pool, minrate=minrate, maxrate=maxrate, expand=expand, shrink=shrink)


# return memcahce policy and capacity for frontend
@manager.route('/memcacheconfig')
def get_memcacheconfig():
    """Configuration page render.

    Args:
      n/a

    Returns:
      json: the arguments for the Jinja template
    """
    memconfig = {
      'policy': policy,
      'capacity': capacity
    }

    return jsonify(memconfig)
  
  
# return scaler settings for auto scaler
@manager.route('/scalerconfig')
def get_scalerconfig():
    """Configuration page render.

    Args:
      n/a

    Returns:
      json: the arguments for the Jinja template
    """
    scalerconfig = {
      'scalerswitch': scalerswitch,
      'minrate': float(int(minrate)/100),
      'maxrate': float(int(maxrate)/100),
      'expand': expand,
      'shrink': shrink
    }
    return jsonify(scalerconfig)


# update memcache policy and capacity
@manager.route('/putMemcacheConfig', methods=['POST'])
def put_memcacheconfig():
    """Configuration page render.

    Args:
      n/a

    Returns:
      json: the arguments for the Jinja template
    """
    global policy
    global capacity
    policy = request.form['policy']
    capacity = request.form['capacity']
    try:
        ipList = managerfunc.get_all_ip()
        for eachIP in ipList:
            response = requests.get("http://" + eachIP + ":5001/refreshConfiguration" + "/" + str(policy) + "/" + str(capacity))
            manager.logger.debug(response.text)
            return render_template('result.html', result='Your Request Has Been Processed :)')
   
    except Exception as error:
        manager.logger.error('\n* Error: ' + str(error))
        return render_template('result.html', result='Something Wrong :(')


# update scaler settings
@manager.route('/putScalerConfig', methods=['POST'])
def put_scalerconfig():
    """Configuration page render.

    Args:
      n/a

    Returns:
      json: the arguments for the Jinja template
    """
    global minrate
    global maxrate
    global expand
    global shrink
    global scalerswitch
    scalerswitch = request.form['switch']
    minrate = request.form['minrate']
    maxrate = request.form['maxrate']
    expand = request.form['expand']
    shrink = request.form['shrink']
    return render_template('result.html', result='Your Request Has Been Processed :)')


# return 1min miss rate for auto scaler to use
@manager.route('/1minmiss')
def get_1minmiss():
    """Configuration page render.

    Args:
      n/a

    Returns:
      json: the arguments for the Jinja template
    """
    missrate = managerfunc.getAggregateMissRate1mins()
    return jsonify(missrate)
    
  
# return number of instance running for auto scaler to use
@manager.route('/numrunning')
def get_num_running():
    """Configuration page render.

    Args:
      n/a

    Returns:
      json: the arguments for the Jinja template
    """
    num = managerfunc.num_running()
    return jsonify(num)
    

# return ip of nth instance for auto scaler to use
@manager.route('/ip/<n>')
def get_nth_ip(n):
    """Return the nth memcache node ip

    Args:
      n/a

    Returns:
      str: the ip address of the nth node
    """
    try:
        ip = managerfunc.get_nth_ip(n)
        return jsonify(ip)
    except Exception as error:
        manager.logger.error('\n* Error: ' + str(error))
        return None


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


@manager.route('/startinstance')
def startinstance():
    try:
        response = managerfunc.start_ec2_instance()
        return response
    except Exception as error:
        manager.logger.error('\n* Error: ' + str(error))
        return None


@manager.route('/stopinstance')
def stopinstance():
    try:
        response = managerfunc.stop_ec2_instance()
        return response
    except Exception as error:
        manager.logger.error('\n* Error: ' + str(error))
        return None


@manager.route('/manualstartinstance', methods=['POST'])
def manualstartinstance():
    global scalerswitch
    scalerswitch = '0'
    try:
        response = managerfunc.start_ec2_instance()
        manager.logger.debug(str(response) + str(scalerswitch))
        return render_template('result.html', result='Your Request Has Been Processed :)')
    except Exception as error:
        manager.logger.error('\n* Error: ' + str(error))
        return render_template('result.html', result='Something Wrong :(')


@manager.route('/manualstopinstance', methods=['POST'])
def manualstopinstance():
    global scalerswitch
    scalerswitch = '0'
    try:
        response = managerfunc.stop_ec2_instance()
        manager.logger.debug(str(response) + str(scalerswitch))
        return render_template('result.html', result='Your Request Has Been Processed :)')
    except Exception as error:
        manager.logger.error('\n* Error: ' + str(error))
        return render_template('result.html', result='Something Wrong :(')
  

@manager.route('/deleteData', methods=['POST'])
def delete_data():
    """Delete the data.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    manager.logger.debug('\n* Deleting data')
    try:
        response = requests.post("http://localhost:5000/api/teardown")
        manager.logger.debug(response.text)
    except Exception as error:
        manager.logger.error('\n* Error: ' + str(error))
    manager.logger.debug('\n* Clearing memcache')
    try:
        ipList = managerfunc.get_all_ip()
        for eachIP in ipList:
            response = requests.get("http://" + eachIP + ":5001/clear")
            manager.logger.debug(response.text)
        return render_template('result.html', result='Your Request Has Been Processed :)')
    except Exception as error:
        manager.logger.error('\n* Error: ' + str(error))
        return render_template('result.html', result='Something Wrong :(')
  

@manager.route('/clearallcache', methods=['POST'])
def clear_all_cache():
    """Clear the memcache.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    manager.logger.debug('\n* Clearing memcache')
    try:
        ipList = managerfunc.get_all_ip()
        for eachIP in ipList:
            response = requests.get("http://" + eachIP + ":5001/clear")
            manager.logger.debug(response.text)
        return render_template('result.html', result='Your Request Has Been Processed :)')
    except Exception as error:
        manager.logger.error('\n* Error: ' + str(error))
        return render_template('result.html', result='Something Wrong :(')
