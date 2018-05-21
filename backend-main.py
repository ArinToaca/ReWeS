import os
import datetime
import string
import random
import base64
import sys
import sqlite3
import time
from flask import jsonify
from flask_cors import CORS, cross_origin
from flask import send_from_directory
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
app = Flask(__name__)  # create the application instance :)
app.config.from_object(__name__)  # load config from this file , flaskr.py
app.config['CORS_HEADERS'] = 'Content-Type'

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'backend.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def epoch_to_iso(seconds):
    return time.strftime('%Y-%m-%dT%H:%M:%SZ',
                         time.localtime(seconds))


def seconds_to_hours(seconds):
    return str(datetime.timedelta(seconds=seconds))


def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    print("executed schema.sql successfully.")
    db.commit()


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

# ROUTES


@app.route('/postdata', methods=['POST'])
@cross_origin()
def insert_by_esp():
    '''method when calling with esp32'''
    db = get_db()
    print("JSON %s" % request.get_json())
    request_dict = request.get_json()
    values = [int(time.time()), request_dict['temperature'],
              request_dict['pressure'], request_dict['humidity']]

    db.execute('insert into weather_history (timestamp, temperature, '
               'pressure, humidity) values (?,?,?,?)', values)
    db.commit()
    return 'OK'


@app.route('/delete', methods=['DELETE'])
@cross_origin()
def delete_by_id():
    '''method when deleting an entry'''
    db = get_db()
    db.execute('delete from weather_history where weather_id == ?',
               [request.args.get('weather_id')])
    db.commit()
    return 'OK'


@app.route('/weather_history', methods=['GET'])
@cross_origin()
def get_by_frontend():
    '''method called by the frontend'''
    db = get_db()
    if request.args.get('limit', False):
        cursor = db.execute('select * from weather_history order by timestamp'
                            'desc limit ?', [request.args.get('limit')])
    else:
        cursor = db.execute('select * from weather_history order by timestamp '
                            'desc')

    columns = [column[0] for column in cursor.description]
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))

    if results:
        return jsonify(results)
    else:
        return 'Empty db.'


if __name__ == '__main__':
    if sys.argv[1] == 'dbinit':
        print("init db")
        with app.app_context():
            init_db()
    elif sys.argv[1] == 'run':
        print('running app...')
        app.run(host='0.0.0.0')
    else:
        raise ValueError("incorrect nr of args!")
