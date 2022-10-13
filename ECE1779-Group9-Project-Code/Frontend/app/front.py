"""
 * front.py
 * front-end interface and router of the gallery web application
 *
 * Author: Weixuan Yang
 * Date: Oct. 11, 2022
"""

from . import gallery
from flask import render_template, request, g, escape
from werkzeug.utils import secure_filename
import mysql.connector
import os
import requests
import base64
from PIL import Image

def get_db():
    """Establish the connection to the database.

    Args:
      n/a

    Returns:
      MySQLConnection: the connector to the available database.
    """
    
    if 'db' not in g:
        g.db = mysql.connector.connect(
            user='root',
            password='199909012',
            host='127.0.0.1',
            database='ece1779'
        )
    return g.db


@gallery.teardown_appcontext
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
    cursor = db_wrapper('get_key')
    Returns:
      str: the arguments for the Jinja template
    """
    gallery.logger.debug('\n* Viewing all image')
    
    db = get_db()
    cursor=db.cursor()
    query = "SELECT id FROM ece1779.memcache_keys;"
    cursor.execute(query)
    
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
    data = {'key': key}
    response = requests.post("http://localhost:5001/get", data=data)
    gallery.logger.debug(response.text)
    if response.json() == 'Unknown key':
        db = get_db()
        cursor=db.cursor()
        
        query = "SELECT value FROM ece1779.memcache_keys WHERE id = %s"
        cursor.execute(query,(key,))
        if not cursor:
            return render_template('result.html', result='Something Wrong :(')
        path = cursor.fetchall()[0][0]
        print(path)
        if not path:
            return render_template('result.html', result='Your Key Is Invalid :(')
        else:
        
            image = base64.b64encode(open(path, 'rb').read()).decode('utf-8')
        data = {'key': key, 'value': image}
        response = requests.post("http://localhost:5001/put", data=data)
        gallery.logger.debug(response.text)
    else:
        image = response.json()
    return render_template('retrieve.html', image='data:image/png; base64, {0}'.format(image), key=escape(key))


@gallery.route('/config')
def get_config():
    """Configuration page render.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
      db = get_db()
    cursor=db.cursor()
    query = "SELECT capacity,lru FROM ece1779.memcache_config WHERE userid = 1;"
    cursor.execute(query)
      cursor = db_wrapper('get_config')
    """
    db = get_db()
    cursor=db.cursor()
    query = "SELECT capacity,lru FROM ece1779.memcache_config WHERE userid = 1;"
    cursor.execute(query)
    
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
    db = get_db()
    cursor=db.cursor()
    query = "SELECT itemNum, totalSize, requestNum, missRate, hitRate FROM ece1779.memcache_stat WHERE userid = 1;"
    cursor.execute(query)
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
    image_file = request.files['image']
    key = request.form['key']
    if len(key)>45:
        return render_template('result.html', result='Key is too long, please input key less than 45 characters.')
    path = os.path.join('app/static/img', secure_filename(key+image_file.filename))
    path = path.replace('\\', '/')
    if len(path)>100:
        return render_template('result.html', result='Key and filename are too long, keep sum of key and filename length under 80 characters.')
    gallery.logger.debug('\n* Uploading an image with key: ' + str(key) + ' and path: ' + str(path))
    if not is_image(image_file):
        return render_template('result.html', result='Please Upload An Image :(')
    image_file.save(path)
    data = {'key': key}
    response = requests.post("http://localhost:5001/get", data=data)
    gallery.logger.debug(response.text)
    if response.json() == 'Unknown key':
       
        db = get_db()
        cursor=db.cursor()
        query = "SELECT id FROM ece1779.memcache_keys;"
        cursor.execute(query)
        if not cursor:
            
            return render_template('result.html', result='Something Wrong :(')
    
        existed=False
        for row in cursor:
            if key in row:
                existed=True
        if not existed:  

            db = get_db()
            cursor=db.cursor()
            query = "INSERT INTO ece1779.memcache_keys  (`id`, `value`) VALUES (%s, %s);"
            cursor.execute(query, (key,path,))
            db.commit()
            
        else:
            
            db = get_db()
            cursor=db.cursor()
            query = "UPDATE ece1779.memcache_keys SET 'value' = %s WHERE 'id' = %s;"
            cursor.execute(query,(path, key,))
            db.commit()
           
            
    else:
        response = requests.get("http://localhost:5001/invalidateKey/%s".format(key))
        gallery.logger.debug(response.text)
        db = get_db()
        cursor=db.cursor()
        query = "UPDATE ece1779.memcache_keys SET value = %s WHERE id = %s;"
        cursor.execute(query,(path, key,))
        db.commit()
        
    if not cursor:
        return render_template('result.html', result='Something Wrong :(')
    image = base64.b64encode(open(path, 'rb').read()).decode('utf-8')
    data = {'key': key, 'value': image}
    
    response = requests.post("http://localhost:5001/put", data=data)
    gallery.logger.debug(response.text)
    return render_template('result.html', result='Your Image Has Been Uploaded :)')


@gallery.route('/putConfig', methods=['POST'])
def put_config():
    """Commit the changes in configurations.

    Args:
      n/a

    Returns:
      str: the arguments for the Jinja template
    """
    
    policy = request.form['policy']
    capacity = request.form['capacity']

    gallery.logger.debug('\n* Configuring with capacity: ' + str(capacity) + ' and policy: ' + str(policy))
    db = get_db()
    cursor=db.cursor()
    query = "UPDATE ece1779.memcache_config SET lru = %s, capacity = %s WHERE userid = 1;"
    cursor.execute(query,(policy, capacity))
    db.commit()
    if not cursor:
        return render_template('result.html', result='Something Wrong :(')
    if request.form['clear']=="yes":
        response = requests.get("http://localhost:5001/clear")
        gallery.logger.debug(response.text)
    response = requests.get("http://localhost:5001/refreshConfiguration")
    gallery.logger.debug(response.text)
    return render_template('result.html', result='Your Configuration Has Been Processed :)')


@gallery.route('/api/upload', methods=['POST'])
def put_image_api():
    """The api to upload an image to the MemCache and database

    Args:
      n/a

    Returns:
      dict: the JSON format response of the HTTP request
    """
    image_file = request.files['file']
    key = request.form['key']
    
            
    path = os.path.join('app/static/img', secure_filename(key+image_file.filename))
    
    gallery.logger.debug('\n* Uploading an image with key: ' + str(key) + ' and path: ' + str(path))
    if len(key)>45:
        return {
            'success': 'false',
            'error': {
                'code': 400,
                'message': 'Bad Request: Key is too long, please input key less than 45 characters.'
            }
        }
    elif len(path)>100:
        return {
            'success': 'false',
            'error': {
                'code': 400,
                'message': 'Bad Request: Key and filename are too long, keep sum of key and filename length under 80 characters.'
            }
        }
         
    if not key:
        return {
            'success': 'false',
            'error': {
                'code': 400,
                'message': 'Bad Request: No valid key input.'
            }
        }
    if not image_file:
        return {
            'success': 'false',
            'error': {
                'code': 400,
                'message': 'Bad Request: No valid image input.'
            }
        }
    if not is_image(image_file):
        return {
            'success': 'false',
            'error': {
                'code': 400,
                'message': 'Bad Request: The uploaded file is not an image.'
            }
        }
    image_file.save(path)
    data = {'key': key}
    response = requests.post("http://localhost:5001/get", data=data)
    gallery.logger.debug(response.text)
    if response.json() == 'Unknown key':
        
        
        db = get_db()
        cursor=db.cursor()
        query = "SELECT id FROM ece1779.memcache_keys;"
        cursor.execute(query)
        if not cursor:
            
            return {
                'success': 'false',
                'error': {
                    'code': 500,
                    'message': 'Internal Server Error: Fail in connecting to database'
                }
            }
    
        existed=False
        for row in cursor:
            if key in row:
                existed=True
        if not existed:  
            db = get_db()
            cursor=db.cursor()
            query = "INSERT INTO ece1779.memcache_keys  (`id`, `value`) VALUES (%s, %s);"
            cursor.execute(query, (key,path,))
            db.commit()
            
        else:
            
            db = get_db()
            cursor=db.cursor()
            query = "UPDATE ece1779.memcache_keys SET 'value' = %s WHERE 'id' = %s;"
            cursor.execute(query,(path, key,))
            db.commit()
    else:
        response = requests.get("http://localhost:5001/invalidateKey/%s".format(key))
        gallery.logger.debug(response.text)
        db = get_db()
        cursor=db.cursor()
        query = "UPDATE ece1779.memcache_keys SET value = %s WHERE id = %s;"
        cursor.execute(query,(path, key,))
        db.commit()
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
    gallery.logger.debug(response.text)
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
    db = get_db()
    cursor=db.cursor()
    query = "SELECT id FROM ece1779.memcache_keys;"
    cursor.execute(query)
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
    
    key = key_value
    gallery.logger.debug('\n* Retrieving an image by key: ' + str(key))
    data = {'key': key}
    response = requests.post("http://localhost:5001/get", data=data)
    gallery.logger.debug(response.text)
    if response.json() == 'Unknown key':
        db = get_db()
        cursor=db.cursor()
        
        query = "SELECT value FROM ece1779.memcache_keys WHERE id = %s"
        cursor.execute(query,(key,))
        if not cursor:
            return {
                'success': 'false',
                'error': {
                    'code': 500,
                    'message': 'Internal Server Error: Fail in connecting to database'
                }
            }
        path = cursor.fetchall()[0][0]
        print(path)
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
        data = {'key': key, 'value': image}
        response = requests.post("http://localhost:5001/put", data=data)
        gallery.logger.debug(response.text)
    else:
        image = response.json()
    return {
        'success': 'true',
        'content': image
    }
    
    