from flask import Flask,render_template,jsonify,request,abort
import json
import requests
import string
import csv
import enum
import sys
app=Flask(__name__)
c=0

#1.Add user!
@app.route("/api/v1/users",methods=["PUT"])
def add_user():
    global c
    c+=1
    usname = request.get_json()['username']
    passw = request.get_json()['password']
    err_code = 400
    if len(str(passw)) != 40:
        return {},400
    for letter in passw:
        if letter not in string.hexdigits:
            return {},400
    payload = {"condition":usname,"condition1":passw,"module":"add_user"}
    response = requests.post('http://52.0.165.28:80/api/v1/db/read', json= payload)
    print("Response got from slave is %r" % response)
    sys.stdout.flush()
    if response.json() == 400 :
        return {},400
    elif response.json() == 201:
        response1 = requests.post('http://52.0.165.28:80/api/v1/db/write', json= payload)
        if response1.json() == 201:
            return{},201
        else:
            return {},400

#2.Delete User!
@app.route("/api/v1/users/<name>",methods=["DELETE"])
def delete_user(name):
    global c
    c+=1
    payload = {"condition":name,"module":"delete_user"}
    response = requests.post('http://52.0.165.28:80/api/v1/db/read', json= payload)
    if response.json() == 400 :
        return {},400
    elif response.json() == 200:
        response1 = requests.post('http://52.0.165.28:80/api/v1/db/write', json= payload)
        if response1.json()==200:
            return {},200
        else:
            return{},400
# list_all_users!
@app.route("/api/v1/users",methods=["GET"])
def list_all_users():
    global c
    c+=1
    payload = {"module":"list_all_users"}
    users = requests.post('http://52.0.165.28:80/api/v1/db/read',json=payload)
    all_users = users.json()
    if all_users != 204:
        users_list = []
        for i in all_users:
            users_list.append(i[0])
        return jsonify(users_list)
    elif all_users == 204:
       return {},204
    else:
        return jsonify(all_users)

# Clear the database!
@app.route("/api/v1/db/clear", methods=["POST"])
def clear_database():
    global c
    c+=1
    payload = {"module":"clear_database"}
    result = requests.post('http://52.0.165.28:80/api/v1/db/write',json=payload)
    if len(result) == 0:
        return {},200
    else:
        return {},405

#counts the request made
@app.route("/api/v1/_count",methods=["GET"])
def count():
    global c
    try:
        return jsonify([c]),200
    except:
        return {},405

#making count as zero
@app.route("/api/v1/_count",methods=["DELETE"])
def count1():
    global c
    c = 0
    if c == 0:
       return jsonify([c]),200

@app.route("/")
def healthCheck():
    return "",200

if __name__=='__main__':
	app.debug=True
	app.run(host='0.0.0.0',port='80')
