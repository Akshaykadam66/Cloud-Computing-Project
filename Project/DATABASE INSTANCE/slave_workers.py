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

# RabbitMq Connnectivity!
connection = pika.BlockingConnection(pika.ConnectionParameters(host='rmq'))
channel = connection.channel()
channel.queue_declare(queue='read_queue')
print('Waiting for ReadQ!')
sys.stdout.flush()
# wait for SynQ from master!
channel.exchange_declare(exchange='logs', exchange_type='fanout')
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange='logs', queue=queue_name)
print('Waiting for SynQ')
sys.stdout.flush()

# Database Connectivity!
connection_db = sqlite3.connect('cloud_slave.db')
cursor = connection_db.cursor()
cursor.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='users' ''')
if cursor.fetchone()[0]!=1:
    sqlite_create_table_query =  '''CREATE TABLE users
                (username varchar(50),
                password varchar(60),
                PRIMARY KEY(username));'''
    cursor.execute(sqlite_create_table_query)
    connection_db.commit()
    print("database created in slave")
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

# When ReadQ is read this function is executed!
def on_request(ch, method, props, body):
    mylist = []
    print("Received in slave from orchestrator %r" % json.loads(body))
    sys.stdout.flush()
    received_data = json.loads(body)
    response_data = 0

    if received_data["module"] == "add_user":
        for keys,values in received_data.items():
                mylist.append(values)
        condition = (mylist[0],)
        query = """SELECT username,password FROM users WHERE username = ?"""
        cursor.execute(query,condition)
        result = cursor.fetchall()
        connection_db.commit()
        print('the cursor.rowcount is %r' % cursor.rowcount)
        if  len(result) == 0:
            print('rowcount is 0')
            sys.stdout.flush()
            response_data = 201
        else:
            print('rowcount is not 0')
            sys.stdout.flush()
            response_data = 400
        print("status code to return is %r" % response_data)
        sys.stdout.flush()

    if received_data["module"] == "list_all_users":
        query = """SELECT username FROM users"""
        cursor.execute(query)
        result = cursor.fetchall()
        connection_db.commit()
        if len(result) == 0:
            # 204 indicates that the request was successfull but there was no content found!
            response_data = 204
        else:
            response_data = result
        print("status code to return is %r" % response_data)
        sys.stdout.flush()

    if received_data["module"] == "delete_user":
        print('inside the if condition of delete_data in slave')
        sys.stdout.flush()
        for keys,values in received_data.items():
                mylist.append(values)
        condition = (mylist[0],)
        query = """SELECT username FROM users WHERE username = ?"""
        cursor.execute(query,condition)
        result = cursor.fetchall()
        connection_db.commit()
        print('the cursor.rowcount is %r' % cursor.rowcount)
        if  len(result) == 0:
            print('rowcount is 0')
            sys.stdout.flush()
            response_data = 400
        else:
            print('rowcount is not 0')
            sys.stdout.flush()
            response_data = 200
        print("status code to return is %r" % response_data)
        sys.stdout.flush()

    if received_data["module"] == "upcoming_ride":
        mylist = []
        for keys,values in received_data.items():
            mylist.append(values)
        condition1 = mylist[0]
        condition2 = mylist[1]
        query = """SELECT rowid,username,time FROM ride WHERE source = ? AND destination = ?"""
        recordTuple = (condition1,condition2)
        cursor.execute(query, recordTuple)
        result = cursor.fetchall()
        connection_db.commit()
        if len(result) == 0:
            # 400 is bad request!
            response_data = 400
        else:
            response_data = result
        print("status code to return is %r" % response_data)
        sys.stdout.flush()


    if received_data["module"] == "ride_details":
        print('inside ride_details of slave')
        sys.stdout.flush()
        mylist = []
        for keys,values in received_data.items():
            mylist.append(values)
        condition = mylist[0]
        query1 = """SELECT rowid,username,time, source, destination FROM ride WHERE rowid = ?"""
        recordTuple = (condition,)
        cursor.execute(query1,recordTuple)
        result = cursor.fetchall()
        connection_db.commit()
        print('select from ride table is executed %r' % result)
        sys.stdout.flush()
        if cursor.rowcount != 0:
            query2 = """SELECT name FROM associated_riders WHERE rowid = ?"""
            recordTuple = (condition,)
            cursor.execute(query2,recordTuple)
            result2 = cursor.fetchall()
            connection_db.commit()
            print('select  from associated_riders fetch value is %r' %result2)
            sys.stdout.flush()
            if cursor.rowcount == 0:
                response_data = result
            else:
                result = result + result2
                response_data = result
        else:
            response_data = 405

    if received_data["module"] == "join_ride":
        # r = json.dumps(received_data)
        print('inside if condition of join_ride in slave')
        sys.stdout.flush()
        mylist = []
        for keys,values in received_data.items():
            mylist.append(values)
        condition1 = mylist[0]
        query = """SELECT rowid FROM ride WHERE rowid =?"""
        cursor.execute(query,condition1)
        print('selecting rideid query executed in slave')
        sys.stdout.flush()
        result = cursor.fetchall()
        connection_db.commit()
        if cursor.rowcount == 0:
            # 405 is method not allowed!
            response_data = 405
        else:
            response_data = 200
        print("status code to return from slave is %r" % response_data)
        sys.stdout.flush()

    if received_data["module"] == "rides_count":
        query = """SELECT COUNT(*) FROM ride"""
        cursor.execute(query)
        result = cursor.fetchall()
        connection_db.commit()
        if len(result) == 0:
            response_data = 405
        else:
            response_data = result
        print("status code to return from slave is %r" % response_data)
        sys.stdout.flush()

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                         props.correlation_id),
                     body=json.dumps(response_data))
    ch.basic_ack(delivery_tag=method.delivery_tag)
    print('Slave wrote to ResponseQ! %r' % response_data)

# when SynQ is read this functions gets executed!
def callback(ch, method, properties, body):
    mylist = []
    print("%r" % json.loads(body))
    sys.stdout.flush()
    print('The payload from the master is received by slave to write into the database')
    sys.stdout.flush()
    payload_to_update = json.loads(body)
    # after getting the payload from master, write the data to the
    # slaves for synchronization and to stay updated!

    if payload_to_update["module"] == "add_user":
        for keys,values in payload_to_update.items():
            mylist.append(values)
        condition1 = mylist[0]
        condition2 = mylist[1]
        query = """INSERT INTO users(username,password)VALUES(?,?)"""
        recordTuple = (condition1,condition2)
        try:
            cursor.execute(query,recordTuple)
            connection_db.commit()
        except sqlite3.IntegrityError:
            print("An Exception was Caught!!")
            sys.stdout.flush()
        print('Slave is updated!')
        sys.stdout.flush()

    if payload_to_update["module"] == "delete_user":
        for keys,values in received_data.items():
            mylist.append(values)
        condition = mylist[0]
        query = """DELETE FROM users WHERE username =?"""
        recordTuple = (condition,)
        cursor.execute(query,recordTuple)
        result = cursor.fetchall()
        connection_db.commit()
        if len(result) == 0:
            response_data = 400
        else:
            response_data = 200
        print("deleted code %r" % response_data)
        sys.stdout.flush()

    if payload_to_update["module"] == "clear_database":
        print('in clear database of slave to update')
        sys.stdout.flush()
        query = """DELETE FROM users"""
        cursor.execute(query)
        result = cursor.fetchall()
        connection_db.commit()
        query1 = """DELETE FROM associated_riders"""
        cursor.execute(query1)
        connection_db.commit()
        result2 = cursor.fetchall()
        query2 = """DELETE FROM ride"""
        cursor.execute(query2)
        result3 = cursor.fetchall()
        connection_db.commit()
        if len(result) == 0 and len(result2) == 0 and len(result3) == 0:
            response_data = 200
        else:
            response_data = 405
        print("status code to return is %r" % response_data)
        sys.stdout.flush()

    if payload_to_update["module"] == "create_ride":
        mylist = []
        print('inside if condition of create_ride in slave')
        for keys,values in payload_to_update.items():
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

    if payload_to_update["module"] == "join_ride":
        print('inside if condition of join_ride in slave to update it!')
        sys.stdout.flush()
        mylist = []
        for keys,values in payload_to_update.items():
            mylist.append(values)
        condition1 =  mylist[0]
        condition2 =  mylist[1]
        query = """INSERT INTO associated_riders(rideid,name)VALUES(?,?)"""
        recordTuple = (condition1,condition2)
        cursor.execute(query,recordTuple)
        print('insert query executed in slave')
        sys.stdout.flush()
        result = cursor.fetchall()
        connection_db.commit()
        if len(result) == 0:
            response_data = 200
        else:
            response_data = 405
            print('slave is updated!')
            sys.stdout.flush()

channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
# Specify quality of service.
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='read_queue', on_message_callback=on_request)

channel.start_consuming()
connection_db.commit()
connection_db.close()


