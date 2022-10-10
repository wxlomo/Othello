from flask import render_template, request, g
from app import webapp
import mysql.connector
import os


def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(
                user='admin',
                password='ece1779',
                host='127.0.0.1',
                database='estore'
        )
    return g.db


@webapp.teardown_appcontext
def teardown_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def db_wrapper(query):
    db = get_db()
    return db.cursor().execute(query)


@webapp.route('/')
def main():
    return render_template('index.html')


@webapp.route('/upload')
def upload():
    return render_template('upload.html')


@webapp.route('/putImage')
def put_image():
    image = request.files['image']
    key = request.form['key']
    path = os.path.join('app/static/img', key)
    image.save(path)
    # invalidate key in memcache
    query = '''INSERT INTO ece1779.memcache_keys (key, value) 
               VALUES (%s, %s);''', (key, path)
    db_wrapper(query)
    return render_template('success.html')


@webapp.route('/view')
def get_all_image():
    query = '''SELECT "key" 
               FROM ece1779.memcache_keys;'''
    return render_template('view.html', cursor=db_wrapper(query))


@webapp.route('/retrieve', methods=['POST'])
def get_image():
    key = request.form['key']
    # find key in memcache
    
    image = ''

    if MISS:
        query = '''SELECT value 
                   FROM ece1779.memcache_keys 
                   WHERE "key" = %s;'''.format(key)
        path = db_wrapper(query).fetchone()[1]
        if not path:
            return render_template('fail.html')
        # put key and image into memcache

    return render_template('retrieve.html', image=image)


@webapp.route('/config')
def get_config():
    query = '''SELECT capacity,lru
               FROM ece1779.memcache_config 
               WHERE userid = 1;'''
    capacity, lru = db_wrapper(query).fetchone()
    if lru == 1:
        return render_template('config.html', policy='LRU', policyi='Random', capa=capacity)
    else:
        return render_template('config.html', policy='Random', policyi='LRU', capa=capacity)


@webapp.route('/putConfig', methods=['POST'])
def put_config():
    query = '''SELECT capacity,lru 
               FROM ece1779.memcache_config 
               WHERE userid = 1;'''
    lru =  db_wrapper(query).fetchone()[1]
    if lru == 1:
        if request.form['policy']: lru == 0
    else:
        if request.form['policy']: lru == 1
    query = '''UPDATE ece1779.memcache_config 
               SET lru = %s, capacity = %s 
               WHERE userid = 1;''', (lru, request.form['capacity'])
    db_wrapper(query)
    if request.form['clear']:
        # clear the memcache
    return render_template('success.html')


@webapp.route('/statistics')
def get_statistics():
    query = '''SELECT itemNum, totalSize, requestNum, missRate, hitRate 
               FROM ece1779.memcache_stat 
               WHERE userid = 1;'''
    return render_template('statistics.html', cursor=db_wrapper(query))


@webapp.route('/about')
def get_about():
    return render_template('about.html')
