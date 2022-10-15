"""
 * frontend.py
 * front-end interface and router of the gallery web application
 *
 * Author: Weixuan Yang
 * Date: Oct. 11, 2022
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


@front.teardown_appcontext
def teardown_db(exception):
    """Close the connection to the database after query executed.

    Args:
      n/a

    Returns:
      n/a
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()


def db_wrapper(query_type, arg1='', arg2=''):
    """Connect to the database and try executing queries in the dict.

    Args:
      query_type (str): the type of the query
      arg1 (str, optional): the first argument in the query
      arg2 (str, optional): the second argument in the query

    Returns:
      MySQLCursor: the cursor contains the requested data, None if query
        type is not in the dict or the execution failed.
    """
    db = get_db()
    if query_type == 'get_key':
        query = "SELECT id FROM gallery.key_mapping;"
    elif query_type == 'get_image':
        query = f"SELECT value FROM gallery.key_mapping WHERE id = '{arg1}'"
    elif query_type == 'get_config':
        query = "SELECT capacity,lru FROM gallery.memcache_config WHERE userid = 1;"
    elif query_type == 'get_statistics':
        query = "SELECT itemNum, totalSize, requestNum, missRate, hitRate FROM gallery.memcache_stat WHERE userid = 1;"
    elif query_type == 'put_image':
        query = f"INSERT INTO gallery.key_mapping  (`id`, `value`) VALUES ('{arg1}', '{arg2}');"
    elif query_type == 'put_image_exist':
        query = f"UPDATE gallery.key_mapping SET value = '{arg2}' WHERE id = '{arg1}';"
    elif query_type == 'put_config':
        query = f"UPDATE gallery.memcache_config SET lru = '{arg1}', capacity = {arg2} WHERE userid = 1;"
    else:
        front.logger.error('\n* Wrong query type: ' + str(query_type))
        return None
    try:
        front.logger.debug('\n* Executing query: ' + str(query))
        cursor = db.cursor()
        cursor.execute(query)
        if query_type == 'put_image' or query_type == 'put_image_exist' or query_type == 'put_config':
            db.commit()
        return cursor
    except mysql.connector.Error as err:
        front.logger.error('\n* Error in executing query: ' + str(err))
        return None


def is_image(file):
    """Check if the file format is an image

    Args:
      file (file): the file object

    Returns:
      bool: true if the format of the file is an image
    """
    return '.' in file.filename and \
           file.filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'tiff', 'gif', 'tif', 'bmp', 'webp', 'png'}


@front.route('/')
def get_home():
    """Home page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    return render_template('index.html')


@front.route('/upload')
def get_upload():
    """Upload page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    return render_template('upload.html')


@front.route('/view')
def get_key():
    """View all page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    front.logger.debug('\n* Viewing all image')
    cursor = db_wrapper('get_key')
    if not cursor:
        return render_template('result.html', result='Something Wrong :(')
    return render_template('view.html', cursor=cursor)


@front.route('/retrieve', methods=['POST'])
def get_image():
    """Retrieve page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
      
    """
    key = request.form['key']
    front.logger.debug('\n* Retrieving an image by key: ' + str(key))
    data = {'key': key}
    response = requests.post("http://localhost:5001/get", data=data)
    front.logger.debug(response.text)
    if response.json() == 'Unknown key':
        cursor = db_wrapper('get_image', key)
        if not cursor:
            return render_template('result.html', result='Something Wrong :(')
        old_path = ''
        for row in cursor:
            old_path = row[0]
        front.logger.debug('\n* Retrieving returns path: ' + str(old_path))
        if not old_path:
            return render_template('result.html', result='Your Key Is Invalid :(')
        else:
            image = base64.b64encode(open(old_path, 'rb').read()).decode('utf-8')
        data = {'key': key, 'value': image}
        response = requests.post("http://localhost:5001/put", data=data)
        front.logger.debug(response.text)
    else:
        image = response.json()
    return render_template('retrieve.html', image='data:image/png; base64, {0}'.format(image), key=escape(key))


@front.route('/config')
def get_config():
    """Configuration page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    cursor = db_wrapper('get_config')
    if not cursor:
        return render_template('result.html', result='Something Wrong :(')
    capacity, policy = cursor.fetchone()
    front.logger.debug('\n* Viewing config with capacity: ' + str(capacity) + ' and policy: ' + str(policy))
    if policy == 'lru':
        return render_template('config.html', poli='LRU', capa=capacity)
    else:
        return render_template('config.html', poli='Random', capa=capacity)


@front.route('/statistics')
def get_statistics():
    """Statistics page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    front.logger.debug('\n* Viewing statistics')
    cursor = db_wrapper('get_statistics')
    if not cursor:
        
        return render_template('result.html', result='Something Wrong :(')
    
    return render_template('statistics.html', cursor=cursor)


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


@front.route('/putImage', methods=['POST'])
def put_image():
    """Commit the page uploading to MemCache and database.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    image_file = request.files['image']
    key = request.form['key']
    path = os.path.join('app/static/img', secure_filename(key) + '.' + image_file.filename.rsplit('.', 1)[1])
    path = path.replace('\\', '/')
    front.logger.debug('\n* Uploading an image with key: ' + str(key) + ' and path: ' + str(path))
    if not is_image(image_file):
        return render_template('result.html', result='Input File Format Is Not Supported :(')
    data = {'key': key}
    response = requests.post("http://localhost:5001/get", data=data)
    front.logger.debug(response.text)
    if response.json() == 'Unknown key':
        cursor = db_wrapper('get_image', key)
        if not cursor:
            return render_template('result.html', result='Something Wrong :(')
        old_path = ''
        for row in cursor:
            old_path = row[0]
        front.logger.debug('\n* Retrieving returns path: ' + str(old_path))
        if not old_path:
            cursor = db_wrapper('put_image', key, path)
        else:
            cursor = db_wrapper('put_image_exist', key, path)
    else:
        response = requests.get("http://localhost:5001/invalidateKey/%s".format(key))
        front.logger.debug(response.text)
        cursor = db_wrapper('put_image_exist', key, path)
    if not cursor:
        return render_template('result.html', result='Something Wrong :(')
    image_file.save(path)
    image = base64.b64encode(open(path, 'rb').read()).decode('utf-8')
    data = {'key': key, 'value': image}
    response = requests.post("http://localhost:5001/put", data=data)
    front.logger.debug(response.text)
    return render_template('result.html', result='Your Image Has Been Uploaded :)')


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
        response = requests.get("http://localhost:5001/clear")
        front.logger.debug(response.text)
    response = requests.get("http://localhost:5001/refreshConfiguration")
    front.logger.debug(response.text)
    return render_template('result.html', result='Your Request Has Been Processed :)')


@front.route('/api/upload', methods=['POST'])
def put_image_api():
    """The api to upload an image to the MemCache and database

    Args:
      n/a

    Returns:
      dict: the JSON format response of the HTTP request
    """
    image_file = request.files['file']
    key = request.form['key']
    path = os.path.join('app/static/img', secure_filename(key) + '.' + image_file.filename.rsplit('.', 1)[1])
    path = path.replace('\\', '/')
    front.logger.debug('\n* Uploading an image with key: ' + str(key) + ' and path: ' + str(path))
    if not key or len(key) > 100:
        return {
            'success': 'false',
            'error': {
                'code': 400,
                'message': 'Bad Request: Input key is invalid.'
            }
        }
    if len(key) > 95:
        return {
            'success': 'false',
            'error': {
                'code': 400,
                'message': 'Bad Request: Input key is too long, it has to shorter than 100 characters.'
            }
        }
    if not image_file or not is_image(image_file):
        return {
            'success': 'false',
            'error': {
                'code': 400,
                'message': 'Bad Request: Input file is invalid.'
            }
        }
    if not is_image(image_file):
        return {
            'success': 'false',
            'error': {
                'code': 400,
                'message': 'Bad Request: Input file format is not supported.'
            }
        }
    image_file.save(path)
    data = {'key': key}
    response = requests.post("http://localhost:5001/get", data=data)
    front.logger.debug(response.text)
    if response.json() == 'Unknown key':
        cursor = db_wrapper('get_image', key)
        if not cursor:
            return {
                'success': 'false',
                'error': {
                    'code': 500,
                    'message': 'Internal Server Error: Fail in connecting to database'
                }
            }
        old_path = ''
        for row in cursor:
            old_path = row[0]
        front.logger.debug('\n* Retrieving returns path: ' + str(old_path))
        if not old_path:
            cursor = db_wrapper('put_image', key, path)
        else:
            cursor = db_wrapper('put_image_exist', key, path)
    else:
        response = requests.get("http://localhost:5001/invalidateKey/%s".format(key))
        front.logger.debug(response.text)
        cursor = db_wrapper('put_image_exist', key, path)
    if not cursor:
        return {
            'success': 'false',
            'error': {
                'code': 500,
                'message': 'Internal Server Error: Fail in connecting to database'
            }
        }
    image = base64.b64encode(open(path, 'rb').read()).decode('utf-8')
    data = {'key': key, 'value': image}
    response = requests.post("http://localhost:5001/put", data=data)
    front.logger.debug(response.text)
    return {
        'success': 'true',
    }


@front.route('/api/list_keys', methods=['POST'])
def get_key_api():
    """The api to view all the keys stored in the database

    Args:
      n/a

    Returns:
      dict: the JSON format response of the HTTP request
    """
    front.logger.debug('\n* Viewing all image')
    keys = []
    cursor = db_wrapper('get_key')
    if not cursor:
        return {
            'success': 'false',
            'error': {
                'code': 500,
                'message': 'Internal Server Error: Fail in connecting to database'
            }
        }
    for row in cursor:
        keys.append(row[0])
    if len(keys) == 0:
        return {
            'success': 'false',
            'error': {
                'code': 404,
                'message': 'Not Found: There is no image in the gallery.'
            }
        }
    else:
        return {
            'success': 'true',
            'keys': keys
        }


@front.route('/api/key/<key_value>', methods=['POST'])
def get_image_api(key_value):
    """The api to retrieve an image by the given key from MemCache or database

    Args:
      n/a

    Returns:
      dict: the JSON format response of the HTTP request
      
    """
    
    key = key_value
    front.logger.debug('\n* Retrieving an image by key: ' + str(key))
    data = {'key': key}
    response = requests.post("http://localhost:5001/get", data=data)
    front.logger.debug(response.text)
    if response.json() == 'Unknown key':
        cursor = db_wrapper('get_image', key)
        if not cursor:
            return {
                'success': 'false',
                'error': {
                    'code': 500,
                    'message': 'Internal Server Error: Fail in connecting to database'
                }
            }
        old_path = ''
        for row in cursor:
            old_path = row[0]
        front.logger.debug('\n* Retrieving returns path: ' + str(old_path))
        if not old_path:
            return {
                'success': 'false',
                'error': {
                    'code': 404,
                    'message': 'Not Found: The given key is invalid.'
                }
            }
        else:
            image = base64.b64encode(open(old_path, 'rb').read()).decode('utf-8')
        data = {'key': key, 'value': image}
        response = requests.post("http://localhost:5001/put", data=data)
        front.logger.debug(response.text)
    else:
        image = response.json()
    return {
        'success': 'true',
        'content': image
    }
