from flask import Flask,render_template,jsonify,request,abort
import pymysql
import sys
import json
import requests
import string
import csv
import enum
app=Flask(__name__)
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
    response_from_micro = requests.get('http://3.214.155.143:80/api/v1/users')
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
            response1 = requests.post('http://52.0.165.28:80/api/v1/db/write', json= payload)
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
    response = requests.post('http://52.0.165.28:80/api/v1/db/read',json=payload)
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
    response = requests.post('http://52.0.165.28:80/api/v1/db/read',json = payload)
    # print(response.json())
    # print(response)
    try:
        data = list(response.json())
        data1 = []
        ass_riders = []
        data1 = data[0]
        ass_riders = data[1]
    except IndexError:
        print('Caught an Exception')
        sys.stdout.flush()
    data11 = {"rideId":data1[0],"Created_by":data1[1],"users":ass_riders,"Timestamp":data1[2],"source":data1[3],"destination":data1[4]}
    return data11

#Clear the database!
@app.route("/api/v1/db/clear", methods=["POST"])
def clear_database():
    global c
    c+=1
    payload = {"module":"clear_database"}
    result = requests.post('http://52.0.165.28:80/api/v1/db/write', json=payload)
    if len(result) == 0:
        return {},200
    else:
        return {},405


#Delete a Ride!
@app.route("/api/v1/rides/<rideid>",methods=["DELETE"])
def delete_ride(rideid):
    global c
    c+=1
    payload = {"condition":rideid,"module":"delete_ride"}
    response = requests.post('http://52.0.165.28:80/api/v1/db/read', json= payload)
    if response.json() == 405:
        return {},response.json()
    else:
        response = requests.post('http://52.0.165.28:80/api/v1/db/write', json=payload)
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
    response_from_micro = requests.get('http://3.214.155.143:80/api/v1/users')
    return_data = response_from_micro.json()
    if user_name not in return_data:
        return {},405
    response=requests.post('http://52.0.165.28:80/api/v1/db/read',json=payload)
    if response.json() == 405:
        return {},response.json()
    response=requests.post('http://52.0.165.28:80/api/v1/db/write',json=payload)
    return {},response.json()


#count rides!
@app.route("/api/v1/rides/count",methods=["GET"])
def rides_count():
    global c
    c+=1
    payload = {"module":"rides_count"}
    response = requests.post('http://52.0.165.28:80/api/v1/db/read',json = payload)
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

@app.route("/")
def HealthChecker():
    return "",200

if __name__=='__main__':
	app.debug=True
	app.run(host='0.0.0.0',port='80')

