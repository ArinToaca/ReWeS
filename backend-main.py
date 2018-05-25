import os
import datetime
import sys
import calendar
import sqlite3
import time
import statistics
from calculations import compare
from meteocalc import dew_point, heat_index, Temp
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


def init_cloud_db():
    db = get_db()
    with app.open_resource('schema_cloud.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    print("executed schema_cloud.sql successfully.")
    db.commit()


def init_rain_db():
    db = get_db()
    with app.open_resource('schema_rain.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    print("executed schema_rain.sql successfully.")
    db.commit()


def init_wind_db():
    db = get_db()
    with app.open_resource('schema_wind.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    print("executed schema_rain.sql successfully.")
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
    values = [calendar.timegm(time.gmtime()),
              request_dict['temperature'],
              request_dict['pressure'],
              request_dict['humidity'],
              dew_point(Temp(request_dict['temperature'], 'c'),
                        request_dict['humidity']).c,
              heat_index(Temp(request_dict['temperature'], 'c'),
                         request_dict['humidity']).c]

    db.execute('insert into weather_history (timestamp, temperature, '
               'pressure, humidity, dew_point, heat_index) values '
               '(?,?,?,?,?,?)', values)

    if request_dict.get('cloud_coverage', False):
        cloudy = request_dict['cloud_coverage']
        cloudy = str(cloudy)[1:]
        db.execute('insert into cloud_history (cloud_coverage,timestamp)'
                   'values (?,?)',
                   [cloudy,
                    calendar.timegm(time.gmtime())])

    if request_dict.get('rain', False):
        rain = request_dict['rain']
        db.execute('insert into cloud_history (rain,timestamp)'
                   'values (?,?)',
                   [rain,
                    calendar.timegm(time.gmtime())])

    if request_dict.get('wind_direction', False):
        wind_direction = request_dict['wind_direction']
        wind_speed = request_dict['wind_speed']
        db.execute('insert into wind_history (wind_direction, wind_speed, '
                   'timestamp) values (?,?,?)',
                   [wind_direction, wind_speed,
                    calendar.timegm(time.gmtime())])

    db.commit()
    return 'OK'


@app.route('/shutdown_raspi', methods=['GET'])
@cross_origin()
def raspi_shutdown():
    return 'yes'


@app.route('/delete', methods=['DELETE'])
@cross_origin()
def delete_by_id():
    '''method when deleting an entry'''
    db = get_db()
    if request.args.get('to_date'):
        db.execute('delete from weather_history where timestamp >= ? '
                   'and timestamp <= ? ',
                   [request.args.get('from_date'),
                    request.args.get('to_date')])
    else:
        db.execute('delete from weather_history where timestamp >= ? '
                   [request.args.get('from_date')])
    db.commit()
    return 'OK'


@app.route('/cloud', methods=['GET'])
@cross_origin()
def cloud():
    '''cloud_coverage'''
    db = get_db()
    if request.method == 'GET':
        if request.args.get('limit', False):
            cursor = db.execute('select * from cloud_history order by '
                                'timestamp desc limit ?',
                                [request.args.get('limit')])
        else:
            cursor = db.execute('select * from cloud_history order by '
                                'timestamp desc ')

        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return jsonify(results)
    return 'OK'


@app.route('/rain', methods=['GET'])
@cross_origin()
def rain():
    '''rain'''
    db = get_db()
    if request.method == 'GET':
        if request.args.get('limit', False):
            cursor = db.execute('select * from rain_history order by '
                                'timestamp desc limit ?',
                                [request.args.get('limit')])
        else:
            cursor = db.execute('select * from rain_history order by '
                                'timestamp desc ')

        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return jsonify(results)
    return 'OK'


@app.route('/wind', methods=['GET'])
@cross_origin()
def wind():
    '''rain'''
    db = get_db()
    if request.method == 'GET':
        if request.args.get('limit', False):
            cursor = db.execute('select * from wind_history order by '
                                'timestamp desc limit ?',
                                [request.args.get('limit')])
        else:
            cursor = db.execute('select * from wind_history order by '
                                'timestamp desc ')

        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return jsonify(results)
    return 'OK'


@app.route('/tendency', methods=['GET'])
@cross_origin()
def get_tendency():
    '''method getting tendency'''
    db = get_db()
    if request.args.get('limit', False):
        cursor = db.execute('select * from weather_history order by timestamp'
                            'desc limit ?', [request.args.get('limit')])
    else:
        cursor = db.execute('select * from weather_history order by timestamp '
                            'desc limit 3')

    columns = [column[0] for column in cursor.description]
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    temp_mean = statistics.mean([el['temperature'] for el in results[1:]])
    hum_mean = statistics.mean([el['humidity'] for el in results[1:]])
    pressure_mean = statistics.mean([el['pressure'] for el in results[1:]])
    diff_temp = compare(results[0]['temperature'], temp_mean)
    diff_pressure = compare(results[0]['pressure'], pressure_mean)
    diff_humidity = compare(results[0]['humidity'], hum_mean)

    final_result = dict()
    final_result['temperature_tendency'] = diff_temp
    final_result['pressure_tendency'] = diff_pressure
    final_result['humidity_tendency'] = diff_humidity

    return jsonify(final_result)


@app.route('/weather_history', methods=['GET'])
@cross_origin()
def get_by_frontend():
    '''method called by the frontend'''
    db = get_db()
    if request.args.get('limit', False):
        cursor = db.execute('select * from weather_history order by timestamp '
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
    elif sys.argv[1] == 'cloudinit':
        with app.app_context():
            init_cloud_db()
    elif sys.argv[1] == 'raininit':
        with app.app_context():
            init_rain_db()
    elif sys.argv[1] == 'windinit':
        with app.app_context():
            init_wind_db()
    else:
        raise ValueError("icorrect nr of args!")
