"""
 * front.py
 * front-end interface and router of the gallery web application
 *
 * Author: Weixuan Yang, Haotian Chen, Haozhe Sun
 * Date: Oct. 11, 2022
"""

from . import gallery
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
            user='admin',
            password='ece1779',
            host='127.0.0.1',
            database='estore'
        )
    return g.db


@gallery.teardown_appcontext
def teardown_db():
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
    query = {
        'get_key': '''SELECT "key" 
                   FROM ece1779.memcache_keys;''',
        'get_image': '''SELECT value 
                        FROM ece1779.memcache_keys 
                        WHERE "key" = %s;'''.format(arg1),
        'get_config': '''SELECT capacity,lru
                         FROM ece1779.memcache_config 
                         WHERE userid = 1;''',
        'get_statistics': '''SELECT itemNum, totalSize, requestNum, missRate, hitRate 
                             FROM ece1779.memcache_stat 
                             WHERE userid = 1;''',
        'put_image': '''INSERT INTO ece1779.memcache_keys (key, value) 
                        VALUES (%s, %s);'''.format(arg1, arg2),
        'put_image_exist': '''UPDATE ece1779.memcache_keys
                              SET value = %s
                              WHERE "key" = %s;'''.format(arg1, arg2),
        'put_config': '''UPDATE ece1779.memcache_config 
                         SET lru = %s, capacity = %s 
                         WHERE userid = 1;'''.format(arg1, arg2)
    }
    db = get_db()
    if query_type not in query:
        gallery.logger.error('\n* Wrong query type: ' + str(query_type))
        return None
    try:
        cursor = db.cursor().execute(query[query_type])
        gallery.logger.debug('\n* Executing query: ' + str(query_type))
        return cursor
    except mysql.connector.Error as err:
        gallery.logger.error('\n* Error in executing query: ' + str(err))
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


@gallery.route('/')
def get_home():
    """Home page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    return render_template('index.html')


@gallery.route('/upload')
def get_upload():
    """Upload page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    return render_template('upload.html')


@gallery.route('/view')
def get_key():
    """View all page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    gallery.logger.debug('\n* Viewing all image')
    cursor = db_wrapper('get_key')
    if not cursor:
        return render_template('result.html', result='Something Wrong :(')
    return render_template('view.html', cursor=cursor)


@gallery.route('/retrieve', methods=['POST'])
def get_image():
    """Retrieve page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    key = request.form['key']
    gallery.logger.debug('\n* Retrieving an image by key: ' + str(key))
    data = dict(key=key)
    response = requests.post("http://localhost:5001/get", data=data)
    gallery.logger.debug(response)
    if response == 'miss':
        cursor = db_wrapper('get_image')
        if not cursor:
            return render_template('result.html', result='Something Wrong :(')
        path = cursor.fetchone()[1]
        if not path:
            return render_template('result.html', result='Your Key Is Invalid :(')
        else:
            image = base64.b64encode(open(path, 'rb').read()).decode('utf-8')
        data = dict(key=key, value=image)
        response = requests.post("http://localhost:5001/put", data=data)
        gallery.logger.debug(response)
    else:
        image = response
    return render_template('retrieve.html', image='data:image/png; base64, {0}'.format(image), key=escape(key))


@gallery.route('/config')
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
    gallery.logger.debug('\n* Viewing config with capacity: ' + str(capacity) + ' and policy: ' + str(policy))
    if policy == 'lru':
        return render_template('config.html', policy='LRU', policyi='Random', capa=capacity)
    else:
        return render_template('config.html', policy='Random', policyi='LRU', capa=capacity)


@gallery.route('/statistics')
def get_statistics():
    """Statistics page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    gallery.logger.debug('\n* Viewing statistics')
    cursor = db_wrapper('get_statistics')
    if not cursor:
        return render_template('result.html', result='Something Wrong :(')
    return render_template('statistics.html', cursor=cursor)


@gallery.route('/about')
def get_about():
    """About page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    gallery.logger.debug('\n* Viewing about')
    return render_template('about.html')


@gallery.route('/putImage', methods=['POST'])
def put_image():
    """Commit the page uploading to MemCache and database.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    image = base64.b64encode(request.files['image'].read()).decode('utf-8')
    key = request.form['key']
    path = os.path.join('app/static/img', secure_filename(key))
    gallery.logger.debug('\n* Uploading an image with key: ' + str(key) + ' and path: ' + str(path))
    if not is_image(image):
        return render_template('result.html', result='Please Upload An Image :(')
    image.save(path)
    data = dict(key=key, value=image)
    response = requests.post("http://localhost:5001/put", data=data)
    gallery.logger.debug(response)
    cursor = db_wrapper('get_image')
    if not cursor:
        return render_template('result.html', result='Something Wrong :(')
    path = cursor.fetchone()[1]
    if not path:
        cursor = db_wrapper('put_image', key, path)
    else:
        cursor = db_wrapper('put_image_exist', key, path)
    if not cursor:
        return render_template('result.html', result='Something Wrong :(')
    return render_template('result.html', result='Your Image Has Been Uploaded :)')


@gallery.route('/putConfig', methods=['POST'])
def put_config():
    """Commit the changes in configurations.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    cursor = db_wrapper('get_config')
    if not cursor:
        return render_template('result.html', result='Something Wrong :(')
    policy = cursor.fetchone()[1]
    if policy == 'lru':
        if request.form['policy']:
            policy = 'random'
    else:
        if request.form['policy']:
            policy = 'lru'
    capacity = request.form['capacity']
    gallery.logger.debug('\n* Configuring with capacity: ' + str(capacity) + ' and policy: ' + str(policy))
    cursor = db_wrapper('put_config', policy, capacity)
    if not cursor:
        return render_template('result.html', result='Something Wrong :(')
    if request.form['clear']:
        response = requests.post("http://localhost:5001/clear")
        gallery.logger.debug(response)
    response = requests.post("http://localhost:5001/refreshConfiguration")
    gallery.logger.debug(response)
    return render_template('result.html', result='Your Configuration Has Been Processed :)')


@gallery.route('/api/upload', methods=['POST'])
def put_image_api():
    """The api to upload an image to the MemCache and database

    Args:
      n/a

    Returns:
      dict: the JSON format response of the HTTP request
    """
    image = request.files['file']
    key = request.form['key']
    path = os.path.join('app/static/img', secure_filename(key))
    gallery.logger.debug('\n* Uploading an image with key: ' + str(key) + ' and path: ' + str(path))
    if not key:
        return {
            'success': 'false',
            'error': {
                'code': 400,
                'message': 'Bad Request: No valid key input.'
            }
        }
    if not image:
        return {
            'success': 'false',
            'error': {
                'code': 400,
                'message': 'Bad Request: No valid image input.'
            }
        }
    if not is_image(image):
        return {
            'success': 'false',
            'error': {
                'code': 400,
                'message': 'Bad Request: The uploaded file is not an image.'
            }
        }
    image.save(path)
    data = dict(key=key, value=image)
    response = requests.post("http://localhost:5001/put", data=data)
    gallery.logger.debug(response)
    cursor = db_wrapper('get_image')
    if not cursor:
        return render_template('result.html', result='Something Wrong :(')
    path = cursor.fetchone()[1]
    if not path:
        cursor = db_wrapper('put_image', key, path)
    else:
        cursor = db_wrapper('put_image_exist', key, path)
    if not cursor:
        return {
            'success': 'false',
            'error': {
                'code': 500,
                'message': 'Internal Server Error: Fail in connecting to database'
            }
        }
    return {
        'success': 'true',
    }


@gallery.route('/api/list_keys', methods=['POST'])
def get_key_api():
    """The api to view all the keys stored in the database

    Args:
      n/a

    Returns:
      dict: the JSON format response of the HTTP request
    """
    gallery.logger.debug('\n* Viewing all image')
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


@gallery.route('/api/key/<key_value>', methods=['POST'])
def get_image_api(key_value):
    """The api to retrieve an image by the given key from MemCache or database

    Args:
      n/a

    Returns:
      dict: the JSON format response of the HTTP request
    """
    gallery.logger.debug('\n* Retrieving an image by key: ' + str(key_value))
    data = dict(key=key_value)
    response = requests.post("http://localhost:5001/get", data=data)
    gallery.logger.debug(response)
    if response == 'miss':
        cursor = db_wrapper('get_image')
        if not cursor:
            return {
                'success': 'false',
                'error': {
                    'code': 500,
                    'message': 'Internal Server Error: Fail in connecting to database'
                }
            }
        path = cursor.fetchone()[1]
        if not path:
            return {
                'success': 'false',
                'error': {
                    'code': 404,
                    'message': 'Not Found: The given key is invalid.'
                }
            }
        else:
            image = base64.b64encode(open(path, 'rb').read()).decode('utf-8')
        data = dict(key=key_value, value=image)
        response = requests.post("http://localhost:5001/put", data=data)
        gallery.logger.debug(response)
    else:
        image = response
    return {
        'success': 'true',
        'content': image
    }
