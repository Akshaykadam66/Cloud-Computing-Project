from flask import Flask,render_template,jsonify,request,abort
import threading
import subprocess
import math
import sys
import json
import requests
import string
import pika
import sys
import time
import uuid
import docker
import os
client = docker.from_env()
#client = docker.DockerClient(base_url='http://52.0.165.28:80')
c = 0
timer = 0
extra_slaves = 0
app=Flask(__name__)
flag = 0

# Define a function to scale!
def scale():
    requests.get('http://127.0.0.1:80/api/v1/scale')

# define the timer to scale after every 2 minutes!
def timer_():
    global flag
    flag = 1
    timer = threading.Timer(120,scale)
    timer.start()
    print('Timer started!')
    sys.stdout.flush()

#Read Data!
@app.route("/api/v1/db/read",methods=["POST"])
def read_data():
    global flag
    if flag == 0:
        timer_()
    received_data = request.get_json()
    print("payload got in read_data %r" % received_data)
    sys.stdout.flush()
    global c
    c = c + 1
    print('Read API was called %r times' % c)
    sys.stdout.flush()
    readthedata_rpc = ReadTheData()
    print('class object is created')
    sys.stdout.flush()
    response = readthedata_rpc.call(received_data)
    print('readthedata class is called')
    sys.stdout.flush()
    # response = json.loads(response)
    print(" [.] Got %r" % response)
    sys.stdout.flush()
    return jsonify(response)

#Write Data!
@app.route("/api/v1/db/write",methods=["POST"])
def write_data():
    received_data = request.get_json()
    print("payload got in write_data %r" % received_data)
    writethedata_rpc = WriteTheData()
    response = writethedata_rpc.call(received_data)
    print(" [.] Got %r" % response)
    return jsonify(response)

# Clear the database!
@app.route("/api/v1/db/clear", methods=["POST"])
def clear_database():
    payload = {"module":"clear_database"}
    print('In clear DB API')
    writethedata_rpc = WriteTheData()
    response = writethedata_rpc.call(payload)
    print("Got %r" % response)
    if response == 405:
        return {},405
    elif response == 200:
        return {},200

# Add a new slave!
@app.route("/api/v1/add_slave",methods=["GET"])
def add_slave():
    print('in add_slave api')
    for i in client.containers.list():
        if i.name == 'slave':
           new_slave_object = i
          # print('new_slave is %r' % new_slave_object)
          # sys.stdout.flush()
    new_slave = new_slave_object.commit()
    new_cont_object = client.containers.run(image=new_slave,network_mode='database_default',command='python slave_workers.py' ,detach=True)
    containers_list = client.containers.list()
    cmd = "docker cp master/cloud_master.db "+str(containers_list[0].id)+":/cc_project"
   # os.system('ls')
    os.system(cmd)
    return jsonify(200)

# Crash Slave!
@app.route("/api/v1/crash/slave", methods=["POST"])
def crash_slave():
    print("inside crash_slave")
    sys.stdout.flush()
    mylist = []
    mydict = {}
    containers_list = client.containers.list()
    for k in containers_list:
        if k.name !='master' and k.name !='orchestrator' and k.name != 'rmq' and k.name != 'slave_new':
            sample = k.attrs
            container_status = sample['State']
            container_pid = container_status['Pid']
            mylist.append(container_pid)
            mydict.update({container_pid:k})
    mylist.sort()
    print("the dictionaryi is %r" % mydict)
    sys.stdout.flush()
    highest_pid = mylist[-1]
    api_to_crash_object = mydict[highest_pid]
    print("the crashed api is %r" % api_to_crash_object.name)
    sys.stdout.flush()
    print('In creating a slave api')
    for i in client.containers.list():
        if i.name == 'slave_new':
           new_slave_object = i
          # print('new_slave is %r' % new_slave_object)
          # sys.stdout.flush()
    new_slave = new_slave_object.commit()
    new_cont_object = client.containers.run(image=new_slave,network_mode='database_default',command='python slave_workers.py' ,detach=True)
    containers_list = client.containers.list()
    cmd = "docker cp master/cloud_master.db "+str(containers_list[0].id)+":/cc_project"
   # os.system('ls')
    os.system(cmd)
    api_to_crash_object.kill()
    return {},200

# Remove Slave!
@app.route("/api/v1/remove_slave", methods=["POST"])
def remove_slave():
    print('remove_slave API is called!')
    sys.stdout.flush()
    removed_slave = []
    data_got = request.get_json()
    slaves_to_remove = data_got["slaves_to_remove"]
    print('slaves to remove %r' % slaves_to_remove)
    sys.stdout.flush()
    for j in range(slaves_to_remove):
        containers_list = client.containers.list()
        if containers_list[0].name !='slave' and containers_list[0].name !='master' and containers_list[0].name !='orchestrator' and containers_list[0].name != 'slave_new':
            removed_slave.append(containers_list[0].name)
            containers_list[0].kill()
    return jsonify(removed_slave)

# Total slaves!
@app.route("/api/v1/total_slaves",methods=["GET"])
def total_slaves():
    slaves = []
    print('in total_slaves api')
    for i in client.containers.list():
        slaves.append(i.name)
    print('total slaves %r' % slaves)
    sys.stdout.flush()
    global extra_slaves
    total_slaves = {'count' : extra_slaves+1}
    slaves.append(total_slaves)
    return jsonify(slaves)

# Scaling!
@app.route("/api/v1/scale",methods=["GET"])
def scale():
    global c
    global extra_slaves
    # Scaling Up Happens Here!
    print('Total requests so far %r' % c)
    sys.stdout.flush()
    if c > 20 :
        required_slaves = c/20
        required_slaves = math.ceil(required_slaves)
        required_slaves = required_slaves - 1
        print('required_slaves (scale up)  %r' % required_slaves)
        print('extra_slaves (scale up) %r' % extra_slaves)
        sys.stdout.flush()
        if required_slaves > extra_slaves:
            print('I need more slaves!')
            sys.stdout.flush()
            needed_slaves = required_slaves - extra_slaves
            extra_slaves  = extra_slaves + needed_slaves
            print('needed_slaves are (scale up) %r' % needed_slaves)
            sys.stdout.flush()
            for i in range(needed_slaves):
                print('Inside for loop for creating Slaves!')
                sys.stdout.flush()
                response = requests.get('http://127.0.0.1:80/api/v1/add_slave')
                response = response.json()
                print('response from add_slave is (scale up) %r' % response)
                sys.stdout.flush()
        else:
            print('slaves are enough!')
            sys.stdout.flush()
    # scale down happens here!
    required_slaves = c/20
    required_slaves = math.ceil(required_slaves)
    print('required_slaves %r' % required_slaves)
    sys.stdout.flush()
    #print('total_running_slaves %r ' % total_running_slaves)
    #sys.stdout.flush()
    if (extra_slaves + 1) > required_slaves:
        print('Need to scale it down!')
        sys.stdout.flush()
        slaves_to_remove = extra_slaves - required_slaves
        slaves_to_remove+=1
        extra_slaves = extra_slaves - slaves_to_remove
        payload = {'slaves_to_remove': slaves_to_remove}
        response = requests.post('http://127.0.0.1:80/api/v1/remove_slave',json=payload)
        print('Removed Slaves are %r' % response.json())
        sys.stdout.flush()
    else:
        print('Scale Down not nescessary!')
        sys.stdout.flush()
    c = 0
    timer_()

# Workers list!
@app.route("/api/v1/worker/list",methods=["GET"])
def Workers_list():
    list = []
    print("inside Workers_list!")
    sys.stdout.flush()
    containers_list = client.containers.list()
    for k in containers_list:
        sample = k.attrs
        container_status = sample['State']
        container_pid = container_status['Pid']
        print(container_pid)
        sys.stdout.flush()
        list.append(container_pid)
    list.sort()
    return jsonify(list)

class ReadTheData(object):

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='rmq'))
        print('rmq connection established')
        self.channel = self.connection.channel()

        self.channel.queue_declare(queue='response_queue', exclusive=True)
        print('response_queue declared ')
        sys.stdout.flush()
        self.channel.basic_consume(
            queue='response_queue',
            on_message_callback=self.on_response,
            auto_ack=True)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = json.loads(body)
            print('read got the response from response_queue %r' % json.loads(body))
            sys.stdout.flush()

    def call(self,received_data):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='read_queue',
            properties=pika.BasicProperties(
                reply_to='response_queue',
                correlation_id=self.corr_id,
            ),
            body=json.dumps(received_data))
        print('wrote to read_queue')
        sys.stdout.flush()
        while self.response is None:
            self.connection.process_data_events()
        self.connection.close()
        return self.response

class WriteTheData(object):

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='rmq'))
        print('connection established')
        self.channel = self.connection.channel()

        self.channel.queue_declare(queue='response_queue', exclusive=True)
        print('response_queue declared ')
        self.channel.basic_consume(
            queue='response_queue',
            on_message_callback=self.on_response,
            auto_ack=True)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            print('write got the response from response_queue %r' % json.loads(body))
            self.response = json.loads(body)


    def call(self,received_data):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='write_queue',
            properties=pika.BasicProperties(
                reply_to='response_queue',
                correlation_id=self.corr_id,
            ),
            body=json.dumps(received_data))
        print('wrote to write_queue')
        while self.response is None:
            self.connection.process_data_events()
        self.connection.close()
        return self.response

if __name__=='__main__':
    app.debug=True
    app.run(host='0.0.0.0',port='80')
