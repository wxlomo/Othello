from . import gallery
from flask import render_template, request, g
from werkzeug.utils import secure_filename
import mysql.connector
import os
import requests
import base64


def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(
                user='admin',
                password='ece1779',
                host='127.0.0.1',
                database='estore'
        )
    return g.db


@gallery.teardown_appcontext
def teardown_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def db_wrapper(query):
    db = get_db()
    return db.cursor().execute(query)


@gallery.route('/')
def main():
    return render_template('index.html')


@gallery.route('/upload')
def upload():
    return render_template('upload.html')


@gallery.route('/putImage', methods=['POST'])
def put_image():
    image = request.files['image']
    key = request.form['key']
    path = os.path.join('app/static/img', secure_filename(key))
    webapp.logger.debug('\n* Uploading an image with key: ' + str(key) + ' and path: ' + str(path))
    image.save(path)
    data = dict(key=key, value=image)
    response = requests.post("http://localhost:5001/put", data=data)
    webapp.logger.debug(response)
    query = '''INSERT INTO ece1779.memcache_keys (key, value) 
               VALUES (%s, %s);''', (key, path)
    db_wrapper(query)
    return render_template('result.html', result='Your Image Has Been Uploaded :)')


@gallery.route('/view')
def get_all_image():
    webapp.logger.debug('\n* Viewing all image')
    query = '''SELECT "key" 
               FROM ece1779.memcache_keys;'''
    return render_template('view.html', cursor=db_wrapper(query))


@gallery.route('/retrieve', methods=['POST'])
def get_image():
    key = request.form['key']
    webapp.logger.debug('\n* Retrieving an image by key: ' + str(key))
    data = dict(key=key)
    response = requests.post("http://localhost:5001/get", data=data)
    webapp.logger.debug(response)
    if response == 'miss':
        query = '''SELECT value 
                   FROM ece1779.memcache_keys 
                   WHERE "key" = %s;'''.format(key)
        path = db_wrapper(query).fetchone()[1]
        if not path:
            return render_template('result.html', result='Your Key Is Invalid :(')
        else:
            image = base64.b64encode(open(path, 'rb').read()).decode('utf-8')
        data = dict(key=key, value=image)
        response = requests.post("http://localhost:5001/put", data=data)
        webapp.logger.debug(response)
    else:
        image = response
    return render_template('retrieve.html', image='data:image/png; base64, {0}'.format(image), key=key)


@gallery.route('/config')
def get_config():
    query = '''SELECT capacity,lru
               FROM ece1779.memcache_config 
               WHERE userid = 1;'''
    capacity, policy = db_wrapper(query).fetchone()
    webapp.logger.debug('\n* Viewing config with capacity: ' + str(capacity) + ' and policy: ' + str(policy))
    if policy == 'lru':
        return render_template('config.html', policy='LRU', policyi='Random', capa=capacity)
    else:
        return render_template('config.html', policy='Random', policyi='LRU', capa=capacity)


@gallery.route('/putConfig', methods=['POST'])
def put_config():
    query = '''SELECT capacity,lru 
               FROM ece1779.memcache_config 
               WHERE userid = 1;'''
    capacity = request.form['capacity']
    policy = db_wrapper(query).fetchone()[1]
    if policy == 'lru':
        if request.form['policy']: policy = 'random'
    else:
        if request.form['policy']: policy = 'lru'
    capacity = request.form['capacity']
    webapp.logger.debug('\n* Configuring with capacity: ' + str(capacity) + ' and policy: ' + str(policy))
    query = '''UPDATE ece1779.memcache_config 
               SET lru = %s, capacity = %s 
               WHERE userid = 1;''', (policy, capacity)
    db_wrapper(query)
    if request.form['clear']:
        response = requests.post("http://localhost:5001/clear")
        webapp.logger.debug(response)
    response = requests.post("http://localhost:5001/refreshConfiguration")
    webapp.logger.debug(response)
    return render_template('result.html', result='Your Configuration Has Been Processed :)')


@gallery.route('/statistics')
def get_statistics():
    webapp.logger.debug('\n* Viewing statistics')
    query = '''SELECT itemNum, totalSize, requestNum, missRate, hitRate 
               FROM ece1779.memcache_stat 
               WHERE userid = 1;'''
    return render_template('statistics.html', cursor=db_wrapper(query))


@gallery.route('/about')
def get_about():
    webapp.logger.debug('\n* Viewing about')
    return render_template('about.html')
