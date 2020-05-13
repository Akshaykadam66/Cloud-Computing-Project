from flask import Flask,render_template,jsonify,request,abort
import pymysql
import json
import requests
import string
import csv
import enum
app=Flask(__name__)


connection = pymysql.connect(host="users_database",passwd="password",database="cloud",port=3306)
cursor = connection.cursor()

#1.Add user!
@app.route("/api/v1/users",methods=["PUT"])
def add_user():
    print("In add_user")
    usname = request.get_json()['username']
    passw = request.get_json()['password']
    err_code = 400
    if len(str(passw)) != 40:
        return {},400
    for letter in passw: 
        if letter not in string.hexdigits: 
            return {},400
    payload = {"condition":usname,"condition1":passw,"module":"add_user"}
    response = requests.post('http://127.0.0.1:80/api/v1/db/read', json= payload)
    if response.json() == 400 :
        return {},400
    elif response.json() == 201:
        response1 = requests.post('http://127.0.0.1:80/api/v1/db/write', json= payload)
        print("response of write_data")
        print(response1.json())
        return {},201

#2.Delete User!
@app.route("/api/v1/users/<name>",methods=["DELETE"])
def delete_data(name):
    payload = {"condition":name,"module":"delete_data"}
    response = requests.post('http://127.0.0.1:80/api/v1/db/read', json= payload)
    if response.json() == 400 :
        return {},400
    elif response.json() == 200:
        response1 = requests.post('http://127.0.0.1:80/api/v1/db/write', json= payload)
        return {},200

    

# list_all_users!equests.exceptions.ConnectionError: HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded
@app.route("/api/v1/users",methods=["GET"])
def list_all_users():
    payload = {"module":"list_all_users"}
    users = requests.post('http://127.0.0.1:80/api/v1/db/read',json=payload)
    all_users = users.json()
    users_list = []
    for i in all_users:
        users_list.append(i[0])
    return jsonify(users_list)


# Clear the database!
@app.route("/api/v1/db/clear", methods=["POST"])
def clear_database():
    # payload = {"module":"clear_database"}
    # result = requests.post('http://127.0.0.1:5000/api/v1/db/write',json=payload)
    print("in clear_database api")
    query = """TRUNCATE table users"""
    cursor.execute(query)
    result = cursor.fetchall()
    if len(result) == 0:
        print("truncated table")
        return {},200
    else:
        print("failed")
        return {},405 

34.224.110.41:8080/api/v1/users
#8.Write Data!
@app.route("/api/v1/db/write",methods=["POST"])
def write_data():
    received_data = request.get_json()
    mylist = [] 

    if received_data["module"] == "add_user":
        for keys,values in received_data.items():
            mylist.append(values)
        condition1 = mylist[0]
        condition2 = mylist[1]
        query = """INSERT INTO users(username,password)VALUES (%s, %s)"""
        recordTuple = (condition1,condition2)
        cursor.execute(query,recordTuple)
        result = cursor.fetchall()
        connection.commit()
        if len(result) == 0:
            return jsonify(201)
        else:
            return jsonify(400)
        
    if received_data["module"] == "delete_data":
        for keys,values in received_data.items():
            mylist.append(values)
        condition = mylist[0]
        query = """DELETE FROM users WHERE username =%s"""
        recordTuple = (condition)
        cursor.execute(query,recordTuple)
        result = cursor.fetchall()
        connection.commit()
        if cursor.rowcount == 0:
            return jsonify(400)
        else:
            return jsonify(200)

    
#9.Read Data!
@app.route("/api/v1/db/read",methods=["POST"])
def read_data():
    received_data = request.get_json()
    mylist = []

    if received_data["module"] == "list_all_users":
        query = """SELECT username from users"""
        cursor.execute(query)
        result = cursor.fetchall()
        connection.commit()
        print(result)
        if len(result) == 0:
            # 204 indicates that the request was successfull but there was no content found!
            return jsonify(204)
        else:
            return jsonify(result)

    if received_data["module"] == "add_user":
        for keys,values in received_data.items():
                mylist.append(values)
        condition = mylist[0]
        query = """SELECT username,password FROM users WHERE  username = %s"""
        cursor.execute(query,condition)
        result = cursor.fetchall()
        if len(result) == 0:
                return jsonify(201)
        else:
                return jsonify(400)
        
    if received_data["module"] == "delete_data":
        for keys,values in received_data.items():
            mylist.append(values)
        condition = mylist[0]
        query = """SELECT username FROM users WHERE username =%s"""
        recordTuple = (condition)
        cursor.execute(query,recordTuple)
        result = cursor.fetchall()
        connection.commit()
        if cursor.rowcount == 0:
                return jsonify(400)
        else:
                return jsonify(200)


if __name__=='__main__':
	app.debug=True
	app.run(host='0.0.0.0',port='80')

connection.commit()
connection.close()
