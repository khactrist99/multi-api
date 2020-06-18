import paho.mqtt.client as mqtt
import time
import json
import threading
import logging
import flask
from flask import request, jsonify

broker="52.187.109.154"
# broker = "13.76.250.158"

mqtt.Client.connected_flag=False #create flag in class
clients = {}
out_queue  = {} 

def on_log(client, userdata, level, buf):
   print(buf)

def on_message(client, userdata, message):
   # time.sleep(1)
   data = str(message.payload.decode("utf-8"))
   # print(json(msg))
   msg = json.loads(data)
   print(msg)
   if out_queue.get(msg["device_id"]):
      out_queue[msg["device_id"]] += msg["values"]
   else:
      out_queue[msg["device_id"]] = msg["values"]
#    out_queue.append(msg)

def on_connect(client, userdata, flags, rc):
    if rc==0:
        client.connected_flag=True #set flag
      #   client.subscribe(topic)
    else:
        print("Bad connection Returned code=",rc)
        client.loop_stop()  

def on_disconnect(client, userdata, rc):
   print("client disconnected ok")

def on_publish(client, userdata, mid):
   time.sleep(1)
   print("In on_pub callback mid= "  ,mid)

def Create_connections(username):
   client = mqtt.Client(username)
   client.connect(broker)           #establish connection
   print("connecting to broker", broker)
      #client.on_log=on_log #this gives getailed logging
   client.on_connect = on_connect
   client.on_disconnect = on_disconnect
      #client.on_publish = on_publish
   client.on_message = on_message
   # clients.append(client)
   clients[username] = client
   client.loop_start()
   while not client.connected_flag:
      time.sleep(0.05)

def connect(username, topic):
   Create_connections(username)
   clients[username].subscribe(topic)
   
# dic = {'lock1': {}, 'lock2': {}}
# gesture = ([ ['10', '12'] ],'abc')  
gesture = {"ges1": ['10', '12']}
gesture = {}
def check_user_gesture(username, topic):
    Create_connections(username)
    clients[username].subscribe(topic)
    time.sleep(5)
    print("out queue:", out_queue)
    out_queue["Light"] = []
    res = False
    if out_queue.get("Light") in gesture.values():
        clients[username].publish("Topic/LightD", "{'device_id': 'Light', 'values': ['255']}")
        res = True
    else:
        clients[username].publish("Topic/LightD", "{'device_id': 'Light', 'values': ['127']}")
        res = False
    clients[username].disconnect()
    clients[username].loop_stop()
    print(res)
    return res

def create_gesture(username, topic, gesture_name):
    Create_connections(username)
    clients[username].subscribe(topic)
    time.sleep(5)
    print(out_queue)
    clients[username].disconnect()
    clients[username].loop_stop()

    gesture[gesture_name] = out_queue.get("Light") 
    out_queue["Light"] = []

    return gesture

def update_gesture(username, topic, gesture_name):
    Create_connections(username)
    clients[username].subscribe(topic)
    time.sleep(5)
    clients[username].disconnect()
    clients[username].loop_stop()
    gesture[gesture_name] = out_queue.get("Light") 
    out_queue["Light"] = []
    

    return gesture

def delete_gesture(username, topic, gesture_name):
    gesture.pop(gesture_name)

    return gesture

def get_gesture():
    return gesture
########################################################################################


app = flask.Flask(__name__)
app.config["DEBUG"] = True
app.config["JSON_SORT_KEYS"] = False
import time


@app.route('/multi/check', methods = ['POST'])
def api_check():
    time.sleep(2)
    result = check_user_gesture("Client1", "Topic/Light")
    time.sleep(2)        
    return jsonify(result)

@app.route('/multi/gesture', methods = ['POST'])
def api_gesture():
    data = request.form
    option = data.get('op')
    gesture_name = data.get('gesture_name')
    if option == 'a':
        #add gesture
        return jsonify(create_gesture("Client1", "Topic/Light", gesture_name))
    elif option == 'u':
        #update gesture
        return jsonify(update_gesture("Client1", "Topic/Light", gesture_name))
    elif option == 'd':
        #delete gesture
        return jsonify(delete_gesture("Client1", "Topic/Light", gesture_name))
    elif option == 'g':
        return jsonify(get_gesture())
    else:
        return jsonify(api_err_400())

@app.errorhandler(400)
def api_err_400():
    return bad_request().get()


class Error():
    def __init__(self,code,mess):
        self.code = code
        self.message = mess
    def get(self):
        return self.message,self.code
    
def bad_request():
    return Error(400,'Bad request')    

app.run()

