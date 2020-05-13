from flask import Flask,render_template,jsonify,request,abort
import pymysql
import sys
import json
import requests
import string
import csv
import enum
app=Flask(__name__)


connection = pymysql.connect(host="ride_database",passwd="password",database="cloud",port=3306)
cursor = connection.cursor()
c = 0

#Create Ride!
@app.route("/api/v1/rides",methods=["POST"])
def create_ride():
    global c
    c=c+1    
    user_name = request.get_json()['created_by']
    time = request.get_json()['timestamp']
    source = request.get_json()['source']
    destination = request.get_json()['destination']
    response_from_micro = requests.get('http://172.17.0.1:8080/api/v1/users')
    return_data = response_from_micro.json()
    if user_name not in return_data:
        return {},405
    else:
        with open('AreaNameEnum.csv') as f:
            reader=csv.reader(f)
            Area_list=list(reader)
            cc=enum.Enum('cc', Area_list)
            count = 0
            count1 = 0
            for status in cc:
                if status.value == source or status.name == str(source):
                        count += 1
                elif status.value == destination or status.name == str(destination):
                        count1 +=1
        if count > 0 and count1 > 0 :
            payload = {"condition":user_name,"condition1":time,"condition2":source,"condition3":destination,"module":"create_ride"}
            response1 = requests.post('http://127.0.0.1:80/api/v1/db/write', json= payload)
            
            if response1.json() == 200:
                return {},201
            else:
                return {},400
        else:
            return "",400


#List of all Upcoming rides!
@app.route("/api/v1/rides",methods=["GET"])
def upcoming_ride():
    global c
    c+=1
    source = request.args.get('source')
    destination = request.args.get('destination')
    if len(source) == 0 and len(destination) == 0:
        return {},400
    payload = {"condition1":source,"condition2":destination,"module":"upcoming_ride"}
    response = requests.post('http://127.0.0.1:80/api/v1/db/read',json=payload)
    
    if response.json() == 400:
        return {},400
    else:
        data = list(response.json())
        returnlist = []
        data1 = []
        # looping through the list of lists, taking one_list at a time 
        # making a dictionary and storing all the dictionaries in a separate
        # return_list
        for k in range(len(data)):
            # data11={} 
           
            one_list = data[k]
            data11 = {"rideId":one_list[0],"username":one_list[1],"timestamp":one_list[2]}
            returnlist.append(data11)

        return jsonify(returnlist),200

       
#All the details of a given ride!
@app.route("/api/v1/rides/<rideid>",methods=["GET"])
def ride_details(rideid):
    global c
    c+=1
    
    payload = {"condition":rideid,"module":"ride_details"}
    response = requests.post('http://127.0.0.1:80/api/v1/db/read',json = payload)
    
    # print(response.json())
    # print(response)
    data = list(response.json())
    data1 = []
    ass_riders = []
    try: 
        data1 = data[0]
        ass_riders = data[1]
    except:IndexError
    data11 = {"rideId":data1[0],"Created_by":data1[1],"users":ass_riders,"Timestamp":data1[2],"source":data1[3],"destination":data1[4]}
    
    received =response.json()
    return data11
	    
#Clear the database!
@app.route("/api/v1/db/clear", methods=["POST"])
def clear_database():
    global c
    c+=1
    
    query = """TRUNCATE table associated_riders"""
    cursor.execute(query)
    result = cursor.fetchall()
    query1 = """TRUNCATE table ride"""
    cursor.execute(query1)
    result2 = cursor.fetchall()
    if len(result) == 0 or len(result2) == 0:
        
        return {},200
    else:
       
        return {},405 


#Delete a Ride!
@app.route("/api/v1/rides/<rideid>",methods=["DELETE"])
def delete_ride(rideid):
    global c
    c+=1
   
    payload = {"condition":rideid,"module":"delete_ride"}
    
    response = requests.post('http://127.0.0.1:80/api/v1/db/read', json= payload)
    
    if response.json() == 405:
        return {},response.json()
    else:
        response = requests.post('http://127.0.0.1:80/api/v1/db/write', json=payload)
        
        if response.json() == 405:
            return {},response.json()
        elif response.json() == 200:
            return {},200

#Joining Existing Ride!
@app.route("/api/v1/rides/<rideid>",methods=["POST"])
def join_ride(rideid):
    global c
    c+=1
    user_name = request.get_json()['username']
    payload = {"condition1":rideid,"condition2":user_name,"module":"join_ride"}
    response_from_micro = requests.get('http://172.17.0.1:8080/api/v1/users')
    return_data = response_from_micro.json()
    if user_name not in return_data:
        return {},405
    response=requests.post('http://127.0.0.1:80/api/v1/db/read',json=payload)
    if response.json() == 405:
        return {},response.json()
    response=requests.post('http://127.0.0.1:80/api/v1/db/write',json=payload)
    return {},response.json()


#count rides!
@app.route("/api/v1/rides/count",methods=["GET"])
def rides_count():
    global c
    c+=1
    payload = {"module":"rides_count"}
    response = requests.post('http://127.0.0.1:80/api/v1/db/read',json = payload)
    if response.json() == 405:
        return jsonify(response.json())
    else:
        result1=response.json()
        return jsonify(result1[0])

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
        



#Write Data!
@app.route("/api/v1/db/write",methods=["POST"])
def write_data():
    received_data = request.get_json()
    mylist = [] 

    if received_data["module"] == "join_ride":
        for keys,values in received_data.items():
            mylist.append(values)
        condition1 =  mylist[0]
        condition2 =  mylist[1]
        query = """INSERT INTO associated_riders(rideid,name)VALUES(%s, %s)"""
        recordTuple = (condition1,condition2)
        cursor.execute(query,recordTuple)
        result = cursor.fetchall()
        connection.commit()
        if len(result) == 0:
            return jsonify(200)
        else:
            return jsonify(405)

    if received_data["module"] == "delete_ride":
        for keys,values in received_data.items():
            mylist.append(values)   
        
        condition =  mylist[0]
        
        query = """DELETE FROM ride WHERE rideid = %s"""
        cursor.execute(query, condition)
        result = cursor.fetchall()
        connection.commit()
        if cursor.rowcount == 0:
            return jsonify(405)
        else:
            return jsonify(200) 
 
    if received_data["module"] == "create_ride":
        for keys,values in received_data.items():
            mylist.append(values)
        condition1 = mylist[0]
        condition2 = mylist[1]
        condition3 = int(mylist[2])
        condition4 = int(mylist[3])
        
        query = """INSERT INTO ride(username,time,source,destination)VALUES(%s, %s, %s, %s)"""
        recordTuple = (condition1,condition2,condition3,condition4)
        cursor.execute(query,recordTuple)
        result = cursor.fetchall()
        connection.commit()
        if cursor.rowcount == 0:
            return jsonify(400)
        else:
            return jsonify(200)
    
#Read Data!
@app.route("/api/v1/db/read",methods=["POST"])
def read_data():
    received_data = request.get_json()
    mylist = []

 
    if received_data["module"] == "upcoming_ride":
        for keys,values in received_data.items():
            mylist.append(values)
        condition1 = mylist[0]
        condition2 = mylist[1]
        
        query = """ SELECT rideid,username,time FROM ride WHERE source = %s AND destination = %s"""
        recordTuple = (condition1,condition2)
        cursor.execute(query, recordTuple)
        result = cursor.fetchall()
       
        connection.commit()
        if len(result) == 0:
            # 400 is bad request!
            return jsonify(400)
        else:
            return jsonify(result)

    if received_data["module"] == "join_ride":
        # r = json.dumps(received_data)
        for keys,values in received_data.items():
            mylist.append(values)
        condition1 = mylist[0]
        condition2 = mylist[1]
       
        query = """SELECT rideid FROM ride WHERE rideid =%s"""
        cursor.execute(query,condition1)
        result = cursor.fetchall()
        connection.commit()
       
        if cursor.rowcount == 0:
            # 405 is method not allowed!
            return jsonify(405)   
        else:
            return jsonify(200)
        
    if received_data["module"] == "delete_ride":
        for keys,values in received_data.items():
            mylist.append(values)
        
        condition =  mylist[0]
        
        query = """SELECT rideid FROM ride WHERE rideid = %s"""
        cursor.execute(query,condition)
        result = cursor.fetchall()
        connection.commit()
        if cursor.rowcount != 0:
                return jsonify(200)
        else:
                return jsonify(405)
    
    if received_data["module"] == "ride_details":
        for keys,values in received_data.items():
            mylist.append(values)
       
        condition = mylist[0]
       
        query1 = """SELECT rideid,username,time, source, destination FROM ride WHERE rideid = %s"""
        recordTuple = (condition)
        cursor.execute(query1,recordTuple)
        result = cursor.fetchall()
        if cursor.rowcount == 0:
            return {},405
        data = list(result)
        data1 = list(data[0])
        query2 = """SELECT name FROM associated_riders WHERE rideid = %s"""
        recordTuple = (condition)
        cursor.execute(query2,recordTuple)
        result2 = cursor.fetchall()
        if cursor.rowcount == 0:
            return {},405
        result = result + result2
        connection.commit()
        return jsonify(result)

    if received_data["module"] == "create_ride":
        for keys,values in received_data.items():
            mylist.append(values)
        condition1 = mylist[0]
       
        
        query = """SELECT username FROM users WHERE username =%s"""
        recordTuple = (condition1)
        cursor.execute(query,recordTuple)
        result = cursor.fetchall()
        
        connection.commit()
        if len(result) == 0:
            return jsonify(400)
        else:
            return jsonify(200)

    if received_data["module"] == "rides_count":

        
      
        query = """SELECT COUNT(*) FROM ride"""
        cursor.execute(query)
        result = cursor.fetchall()
       
       
        connection.commit()
        if len(result) == 0:
            return jsonify(405)
        else:
            return jsonify(result)
            return jsonify(200)

        
if __name__=='__main__':
	app.debug=True
	app.run(host='0.0.0.0',port='80')

connection.commit()
connection.close()
