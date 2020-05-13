import pika
import time
import pymysql
import sys
import json
import requests
import string
import csv
import enum
import uuid
import sqlite3
connection_db = sqlite3.connect('master/cloud_master.db')
cursor = connection_db.cursor()

cursor.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='users' ''')
if cursor.fetchone()[0]!=1:
    sqlite_create_table_query = '''CREATE TABLE users
                (username varchar(50),
                password varchar(60),
                PRIMARY KEY(username));'''
    cursor.execute(sqlite_create_table_query)
    connection_db.commit()
    print("database created in master")
    sys.stdout.flush()

cursor.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='ride' ''')
if cursor.fetchone()[0]!=1:
    sqlite_create_table_query = '''CREATE TABLE ride 
                                    (username varchar(50),
                                    time varchar(50),
                                    source varchar(80),
                                    destination varchar(80),
                                    rideid int,
                                    PRIMARY KEY(rideid));'''
    cursor.execute(sqlite_create_table_query)
    connection_db.commit()
    print("ride table created in master")
    sys.stdout.flush()

cursor.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='associated_riders' ''')
if cursor.fetchone()[0]!=1:
    sqlite_create_table_query = '''CREATE TABLE associated_riders
                                    (rideid int,
                                    name varchar(50));'''
    cursor.execute(sqlite_create_table_query)
    connection_db.commit()
    print("associated_riders table created in master")
    sys.stdout.flush()

connection = pika.BlockingConnection(pika.ConnectionParameters(host='rmq'))
channel = connection.channel()

channel.queue_declare(queue='write_queue')
print('Master is Waiting for messages from orchestrator!')
sys.stdout.flush()

def on_request(ch, method, props, body):
    response_data = 0
    print("Received data in callback_function of master %r" % json.loads(body))
    sys.stdout.flush()
    received_data = json.loads(body)
    mylist = []
    if received_data["module"] == "add_user":
        for keys,values in received_data.items():
            mylist.append(values)
        condition1 = mylist[0]
        condition2 = mylist[1]
        response_data = 201
        query = """INSERT INTO users(username,password)VALUES(?,?)"""
        recordTuple = (condition1,condition2)
        try:
            cursor.execute(query,recordTuple)
            connection_db.commit()
        except sqlite3.IntegrityError:
            response_data = 400
        print("status code to return is %r" % response_data)
        sys.stdout.flush()

    if received_data["module"] == "delete_user":
        for keys,values in received_data.items():
            mylist.append(values)
        condition = mylist[0]
        query = """DELETE FROM users WHERE username =?"""
        recordTuple = (condition,)
        cursor.execute(query,recordTuple)
        result = cursor.fetchall()
        connection_db.commit()
        if len(result) == 0:
            response_data = 200
        else:
            response_data = 400
        print("status code to return is %r" % response_data)
        sys.stdout.flush()

    if received_data["module"] == "clear_database":
        print('inside the if condition of master')
        sys.stdout.flush()
        query = """DELETE FROM users"""
        cursor.execute(query)
        result = cursor.fetchall()
        connection_db.commit()
        if len(result) == 0:
            response_data = 200
        else:
            response_data = 405
        print("status code to return is %r" % response_data)
        sys.stdout.flush()

    if received_data["module"] == "create_ride":
        print('inside the create_ride if condition of master')
        for keys,values in received_data.items():
            mylist.append(values)
        condition1 = mylist[0]
        condition2 = mylist[1]
        condition3 = int(mylist[2])
        condition4 = int(mylist[3])
        query = """INSERT INTO ride(username,time,source,destination)VALUES(?, ?,?,?)"""
        recordTuple = (condition1,condition2,condition3,condition4)
        cursor.execute(query,recordTuple)
        result = cursor.fetchall()
        connection_db.commit()
        if cursor.rowcount == 0:
            response_data = 400
        else:
            response_data = 200
        print("status code to return is %r" % response_data)
        sys.stdout.flush()

    if received_data["module"] == "join_ride":
        print('inside if condition of join_ride in master')
        sys.stdout.flush()
        mylist = []
        for keys,values in received_data.items():
            mylist.append(values)
        condition1 =  mylist[0]
        condition2 =  mylist[1]
        query = """INSERT INTO associated_riders(rideid,name)VALUES(?,?)"""
        recordTuple = (condition1,condition2)
        cursor.execute(query,recordTuple)
        print('insert query executed in master')
        sys.stdout.flush()
        result = cursor.fetchall()
        connection_db.commit()
        if len(result) == 0:
            response_data = 200
        else:
            response_data = 405
        print("status code to return is %r" % response_data)
        sys.stdout.flush()

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                         props.correlation_id),
                     body=json.dumps(response_data))
    ch.basic_ack(delivery_tag=method.delivery_tag)
    print('master response_data was wrote on the response_queue and returned successfully')
    print(" [x] Done")
    sys.stdout.flush()
    channel.exchange_declare(exchange='logs', exchange_type='fanout')
    channel.basic_publish(exchange='logs', routing_key='', body=json.dumps(received_data))
    print('wrote data to synQ')
    sys.stdout.flush() 

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='write_queue', on_message_callback=on_request)

channel.start_consuming()
connection_db.commit()
connection_db.close()
