"""
 * frontend.py
 * front-end interface and router of the gallery web application
 *
 * Author: Weixuan Yang
 * Date: Oct. 11, 2022
"""
from . import front, config, s3
from flask import render_template, request, g, escape, jsonify
from werkzeug.utils import secure_filename
import mysql.connector
import requests
import base64
import hashlib


def get_db():
    """Establish the connection to the database on rds.

    Args:
      n/a

    Returns:
      MySQLConnection: the connector to the available database.
    """
    if 'db' not in g:
        try:
            g.db = mysql.connector.connect(
                user=config.rds_config['user'],
                password=config.rds_config['password'],
                host=config.rds_config['host'],
                database=config.rds_config['database']
            )
        except Exception as error:
            front.logger.error('\n* Error in connecting to rds: ' + str(error))
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
        query = f"SELECT value FROM gallery.key_mapping WHERE id = '{arg1}';"
    elif query_type == 'put_image':
        query = f"INSERT INTO gallery.key_mapping  (`id`, `value`) VALUES ('{arg1}', '{arg2}');"
    elif query_type == 'put_image_exist':
        query = f"UPDATE gallery.key_mapping SET value = '{arg2}' WHERE id = '{arg1}';"
    elif query_type == 'clear_key':
        query = "DELETE FROM gallery.key_mapping;"
    else:
        front.logger.error('\n* Wrong query type: ' + str(query_type))
        return None
    try:
        front.logger.debug('\n* Executing query: ' + str(query))
        cursor = db.cursor()
        cursor.execute(query)
        if query_type != 'get_key' and query_type != 'get_image':
            db.commit()
        return cursor
    except Exception as error:
        front.logger.error('\n* Error in executing query: ' + str(error))
        return None


def memcache_request(request_str, key, data=''):
    """Send the HTTP requests to memcache pool

        Args:
          request_str (str): the request to be sent
          key (str): the key to find the designated memcache node
          data (dir, optional): the data attached to the request

        Returns:
          requests.Response object: the response of the request, none if error
    """
    request_partition = int(hashlib.md5(key.encode()).hexdigest(), 16) // 0x10000000000000000000000000000000
    response = requests.get("http://localhost:5002/numrunning")
    n_running = response.json()
    if n_running != 0:
        request_pooling = request_partition % int(n_running)
        response = requests.get("http://localhost:5002/ip/"+str(request_pooling))
        pool_ip = str(response.json())
        if request_str=="invalidateKey/":
            try:
                response = requests.get("http://"+str(pool_ip)+":5001/invalidateKey/"+ str(key))
                return response.text
            except Exception as error:
                front.logger.error('\n* Error in sending request to ' + str(pool_ip) + ', get: ' + str(error))
                return None
        else:
            try:
                response = requests.post("http://"+str(pool_ip)+":5001/" + str(request_str), data=data)
                return response.json()
            except Exception as error:
                front.logger.error('\n* Error in sending request to ' + str(pool_ip) + ', get: ' + str(error))
                return None
    return 'Unknown key'


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
    
    response = memcache_request('get', key, {'key': key})  # retrieve the image by key from memcache
    
    if not response:
        return render_template('result.html', result='Something Wrong :(')
    if response == 'Unknown key':  # if not in memcache
        cursor = db_wrapper('get_image', key)
        if not cursor:
            return render_template('result.html', result='Something Wrong :(')
        filename = ''
        for row in cursor:
            filename = row[0]
        front.logger.debug('\n* Retrieving returns filename: ' + str(filename))
        if not filename:  # the key is either not in database
            return render_template('result.html', result='Your Key Is Invalid :(')
        try:  # the key is in database
            image = base64.b64encode(
                s3.get_object(Bucket=config.s3_config['name'], Key=filename)['Body'].read()).decode("utf-8")
        except Exception as error:
            front.logger.debug('\n* Error: ' + str(error))
            return render_template('result.html', result='Something Wrong :(')
        response = memcache_request('put', key, {'key': key, 'value': image})  # cache the key and image
        
        if not response:
            return render_template('result.html', result='Something Wrong :(')
    else:  # if in memcache
        image = response
    return render_template('retrieve.html', image='data:image/*; base64, {0}'.format(image), key=escape(key))


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
    """Commit the page uploading to MemCache and s3.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    image_file = request.files['image']
    image_file.filename = secure_filename(image_file.filename)
    key = request.form['key']
    front.logger.debug('\n* Uploading an image' + str(image_file.filename) + ' with key: ' + str(key))
    if not is_image(image_file):
        return render_template('result.html', result='Input File Format Is Not Supported :(')
    response = memcache_request('get', key, {'key': key})  # retrieve the image by key from memcache
    
    if not response:
        return render_template('result.html', result='Something Wrong :(')
    if response == 'Unknown key':  # if not in memcache
        cursor = db_wrapper('get_image', key)
        if not cursor:
            return render_template('result.html', result='Something Wrong :(')
        filename = ''
        for row in cursor:
            filename = row[0]
        front.logger.debug('\n* Retrieving returns filename: ' + str(filename))
        if not filename:  # the key is either not in database
            cursor = db_wrapper('put_image', key, image_file.filename)  # insert the key and filename to database
        else:  # the key is in database
            cursor = db_wrapper('put_image_exist', key, image_file.filename)  # update the filename in the database
    else:  # the key is in memcache
        response = memcache_request('invalidateKey/', key)  # invalidate the existed key
        front.logger.debug(response)
        if not response:
            return render_template('result.html', result='Something Wrong :(')
        cursor = db_wrapper('put_image_exist', key, image_file.filename)  # update the filename in the database
    if not cursor:
        return render_template('result.html', result='Something Wrong :(')
    try:
        s3.put_object(Bucket=config.s3_config['name'], Key=image_file.filename, Body=image_file)
    except Exception as error:
        front.logger.debug('\n* Error: ' + str(error))
        return render_template('result.html', result='Something Wrong :(')
    return render_template('result.html', result='Your Image Has Been Uploaded :)')


@front.route('/api/upload', methods=['POST'])
def put_image_api():
    """The api to upload an image to the MemCache and s3

    Args:
      n/a

    Returns:
      dict: the JSON format response of the HTTP request
    """
    image_file = request.files['file']
    image_file.filename = secure_filename(image_file.filename)
    key = request.form['key']
    front.logger.debug('\n* Uploading an image' + str(image_file.filename) + ' with key: ' + str(key))
    if not key:
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
    if not image_file:
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
    response = memcache_request('get', key, {'key': key})  # retrieve the image by key from memcache
    front.logger.debug(response)
    if not response:
        return render_template('result.html', result='Something Wrong :(')
    if response == 'Unknown key':  # if not in memcache
        cursor = db_wrapper('get_image', key)
        if not cursor:
            return {
                'success': 'false',
                'error': {
                    'code': 500,
                    'message': 'Internal Server Error: Fail in connecting to rds'
                }
            }
        filename = ''
        for row in cursor:
            filename = row[0]
        front.logger.debug('\n* Retrieving returns filename: ' + str(filename))
        if not filename:  # the key is either not in database
            cursor = db_wrapper('put_image', key, image_file.filename)  # insert the key and filename to database
        else:  # the key is in database
            cursor = db_wrapper('put_image_exist', key, image_file.filename)  # update the filename in the database
    else:  # the key is in memcache
        response = memcache_request('invalidateKey/', key)  # invalidate the existed key
        front.logger.debug(response)
        if not response:
            return render_template('result.html', result='Something Wrong :(')
        cursor = db_wrapper('put_image_exist', key, image_file.filename)  # update the filename in the database
    if not cursor:
        return {
            'success': 'false',
            'error': {
                'code': 500,
                'message': 'Internal Server Error: Fail in connecting to rds'
            }
        }
    try:
        s3.put_object(Bucket=config.s3_config['name'], Key=image_file.filename, Body=image_file)
    except Exception as error:
        front.logger.debug('\n* Error: ' + str(error))
        return {
            'success': 'false',
            'error': {
                'code': 500,
                'message': 'Internal Server Error: s3 error, ' + str(error)
            }
        }
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
                'message': 'Internal Server Error: Fail in connecting to rds'
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
      key_value (str): the key of the image

    Returns:
      dict: the JSON format response of the HTTP request
      
    """
    
    key = key_value
    front.logger.debug('\n* Retrieving an image by key: ' + str(key))
    response = memcache_request('get', key, {'key': key})  # retrieve the image by key from memcache
    front.logger.debug(response)
    if not response:
        return render_template('result.html', result='Something Wrong :(')
    if response == 'Unknown key':  # if not in memcache
        cursor = db_wrapper('get_image', key)
        if not cursor:
            return {
                'success': 'false',
                'error': {
                    'code': 500,
                    'message': 'Internal Server Error: Fail in connecting to rds'
                }
            }
        filename = ''
        for row in cursor:
            filename = row[0]
        front.logger.debug('\n* Retrieving returns filename: ' + str(filename))
        if not filename:  # the key is either not in database
            return {
                'success': 'false',
                'error': {
                    'code': 404,
                    'message': 'Not Found: The given key is invalid.'
                }
            }
        try:  # the key is in database
            image = base64.b64encode(
                s3.get_object(Bucket=config.s3_config['name'], Key=filename)['Body'].read()).decode("utf-8")
        except Exception as error:
            front.logger.debug('\n* Error: ' + str(error))
            return {
                'success': 'false',
                'error': {
                    'code': 500,
                    'message': 'Internal Server Error: s3 error, ' + str(error)
                }
            }
        response = memcache_request('put', key, {'key': key, 'value': image})
        front.logger.debug(response)
        if not response:
            return render_template('result.html', result='Something Wrong :(')
    else:  # the key is in memcache
        image = response
    return {
        'success': 'true',
        'content': image
    }


@front.route('/api/teardown', methods=['POST'])
def teardown_api():
    """The api to get rid of the data in RDS and S3

    Args:
      n/a

    Returns:
      dict: the JSON format response of the HTTP request

    """
    front.logger.debug('\n* Deleting images from s3...')
    try:
        response = s3.list_objects_v2(Bucket=config.s3_config['name'])
        if 'Content' in response:  # bucket is not empty
            for obj in response['Content']:
                front.logger.debug('  Deleting: ' + str(obj['Key']))
                s3.delete_objects(Bucket=config.s3_config['name'], Delete={'Objects': [{'Key': obj['Key']}]})
        else:  # bucket is empty
            front.logger.debug('  Bucket is empty')
    except Exception as error:
        front.logger.debug('\n* Error: ' + str(error))
        return {
            'success': 'false',
            'error': {
                'code': 500,
                'message': 'Internal Server Error: s3 error, ' + str(error)
            }
        }
    front.logger.debug('\n* Clearing RDS database...')
    cursor = db_wrapper('clear_key')
    if not cursor:
        return {
            'success': 'false',
            'error': {
                'code': 500,
                'message': 'Internal Server Error: Fail in connecting to rds'
            }
        }
    return {
        'success': 'true'
    }
