import httplib
import json
import random
import logging
import threading
import socket
import paho.mqtt.client as mqtt
#import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

class ThingPlug(object):
    def __init__(self,host,port):
        self.ukey = ''
        self.user_id = ''
        self.user_pw = ''
        self.mqtt_client_id = ''
        self.host = host
        self.port = port
        self.deviceList = []
        self.deviceCnt = 0
        self.mqttc = None
        self.mqttc_thread = None
        return
    
    def __del__(self):
        self.mqttDisconnect()
         
    
    def http_connect(self):
        self.conn = httplib.HTTPConnection(self.host,self.port)
    
    def http_close(self):
        self.conn.close()
        
    def login(self,user_id, user_pw): 
        self.user_id = user_id
        self.user_pw = user_pw
        self.ukey = ""
        
        htt_header = {"password" : self.user_pw,
                      "user_id" : self.user_id,
                      "Accept": "application/json"
                      }
        
        self.http_connect()
        self.conn.request("PUT","/ThingPlug?division=user&function=login", "", htt_header)
        resp_data = self.conn.getresponse()
        
        if resp_data.status != 200:
            logging.warning('status :' + resp_data.status)
            self.http_close()
            return False

        json_body = json.loads(resp_data.read())
        if json_body['result_code'] != '200':
            logging.warning("Login Fail[result code : " + json_body['result_code'] + "]")
            self.http_close()
            return False
        
        self.ukey = json_body['userVO']['uKey']
        logging.info("Login Success")

        self.http_close()
        return True
    
    def getDeviceList(self):
        if len(self.ukey) == 0:
            logging.warning('Invalid user key')
            return False
        
        headers = {"uKey" : self.ukey,
                   "Accept": "application/json"
                   }

        query = "/ThingPlug?division=searchDevice&function=myDevice&startIndex=1&countPerPage=5"
        self.http_connect()
        self.conn.request("GET",query,"", headers)
        resp_data = self.conn.getresponse()
        
        if resp_data.status != 200:
            logging.warning('status :' + resp_data.status)
            self.http_close()
            return False

        json_body = json.loads(resp_data.read())
        if json_body['result_code'] != '200':
            logging.warning("getDeviceList Fail[result code : " + json_body['result_code'] + "]")
            self.http_close()
            return False

        self.deviceCnt = json_body['total_list_count']
        
        self.deviceList = []
        for i in range(int(self.deviceCnt)):
            self.deviceList.append(json_body['deviceSearchAPIList'][i]['device_Id'])
            logging.info(json_body['deviceSearchAPIList'][i]['device_Id'])
        
        self.http_close()
        return True, self.deviceCnt, self.deviceList
    
    def getLatestData(self,node_id,container):
        headers = {"Connection" : "keep-alive",
                   "uKey" : self.ukey,
                   "X-M2M-Origin" : node_id,
                   "X-M2M-RI" : node_id + "_" + str(random.randrange(1000,1100)),
                   "Accept": "application/json"
                   }
        
        query = "/ThingPlug/v1_0/remoteCSE-"+ node_id + "/container-" + container + "/latest"
        self.http_connect()
        self.conn.request("GET",query,"", headers)
        
        resp_data = self.conn.getresponse()
        if resp_data.status != 200:
            logging.warning('status :' + str(resp_data.status))
            self.http_close()
            return False

        json_body = json.loads(resp_data.read())
        self.http_close()
        return True,json_body['cin']['con']
    
    def createSubscription(self, node_id, subs_name, container_name, noti_client_id):
        if len(self.ukey) == 0:
            logging.warning('Invalid user key')
            return False

        headers = {"Accept": "application/json",
                   "X-M2M-Origin" : node_id,
                   "X-M2M-RI" : node_id + "_" + str(random.randrange(1000,1100)),
                   "X-M2M-NM" : subs_name,
                   "Content-Type" : "application/vnd.onem2m-res+xml;ty=23",
                   "uKey" : self.ukey
                   }

        payload =  "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" + \
                    "<m2m:sub \n" + \
                    "    xmlns:m2m=\"http://www.onem2m.org/xml/protocols\" \n" + \
                    "    xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">\n" + \
                    "    <enc>\n" + \
                    "         <rss>1</rss>\n" + \
                    "    </enc>\n" + \
                    "    <nu>MQTT|" + noti_client_id + "</nu>\n" + \
                    "    <nct>1</nct>\n" + \
                    "</m2m:sub>"

        query = '/ThingPlug/v1_0/remoteCSE-' + node_id + '/container-' + container_name
        self.http_connect()
        self.conn.request("POST",query,payload, headers)
         
        resp_data = self.conn.getresponse()
        
        if resp_data.status != 201:
            resp_header = resp_data.getheaders()
            logging.warning(resp_header[0][1])
            self.http_close()
            return False
            
        self.http_close()
        logging.info('subscription is created')
        return True
        
    def retrieveSubscription(self, node_id, subs_name, container_name):
        if len(self.ukey) == 0:
            logging.warning('Invalid user key')
            return False

        headers = {"Accept": "application/json",
           "X-M2M-Origin" : node_id,
           "X-M2M-RI" : node_id + "_" + str(random.randrange(1000,1100)),
           "uKey" : self.ukey
           }
  
        query = '/ThingPlug/v1_0/remoteCSE-' + node_id + '/container-' + container_name + '/subscription-' + subs_name
        self.http_connect()
        self.conn.request("GET",query,"", headers)
         
        resp_data = self.conn.getresponse()
        
        if resp_data.status != 200:
            resp_header = resp_data.getheaders()
            logging.warning(resp_data.status)
            logging.warning(resp_header[0][1])
            self.http_close()
            return False
        else:
            logging.info('registered subscription')
            self.http_close()
            return True
    
    def deleteSubscription(self, node_id, subs_name, container_name):
        if len(self.ukey) == 0:
            logging.warning('Invalid user key')
            return False

        headers = {
            'accept': "application/json",
            'x-m2m-ri': node_id + "_" + str(random.randrange(1000,1100)),
            'x-m2m-origin': node_id,
            'ukey': self.ukey,
            'content-type': "application/vnd.onem2m-res+xml;ty=23",
            }
        
        query = "/ThingPlug/v1_0/remoteCSE-" + node_id + "/container-" + container_name + "/subscription-" + subs_name
        self.http_connect()
        self.conn.request("DELETE",query, "", headers)
        resp_data = self.conn.getresponse()
        
        if resp_data.status != 200:
            resp_header = resp_data.getheaders()
            logging.warning(resp_data.status)
            logging.warning(resp_header[0][1])
        else:
            logging.info('subscription is deleted')

        self.http_close()
        
    def getUserId(self):
        return self.user_id
    
    def getUserPw(self):
        return self.user_pw
    
    def getuKey(self):
        return self.ukey

    def mqttConnect(self):
        if self.mqttc != None:
            self.mqttc.reinitialise(self.mqtt_client_id)
        else:
            self.mqttc = mqtt.Client(self.mqtt_client_id)
        
        self.mqttc.on_connect = self.mqtt_on_connect
        self.mqttc.on_message = self.mqtt_on_message
        
        try:
            self.mqttc.username_pw_set(self.getUserId(), self.getuKey())
            self.mqttc.connect(self.host, 1883, 60)
            
            subs_topic = '/oneM2M/req/+/' + self.mqtt_client_id
            self.mqttSubscribe(subs_topic)
        except:
            return
        
#         self.mqttc_thread = threading.Thread(name = 'mqtt_thread', target = self.mqttLoopForever())
#         self.mqttc_thread.start()
        
    def mqttDisconnect(self):
        if self.mqttc == None:
            return False
        
        self.mqttc.disconnect()
        self.mqttc.loop_stop()
    
    def mqttLoopForever(self):
        self.mqttc.loop_forever()
        
    def mqtt_on_connect(self, mqttc, userdata, flags, rc):
        logging.info('mqtt connected')
        
    def mqtt_on_message(self, mqttc, userdata, msg):
        logging.info(msg.topic)
        logging.info(msg.payload)
    
        try:
            xml_root = BeautifulSoup(msg.payload,'html.parser')
            data_payload = getattr(xml_root.find('pc').find('cin').find('con'), 'string', None)
            data = data_payload.decode('hex')
            self.sendDataToDataServer(data)
        except:
            logging.warning(data_payload)
            return
        
    def mqttSubscribe(self,topic):
        self.mqttc.subscribe(topic)
        
    def setMqttClientId(self, client_id):
        self.mqtt_client_id = client_id
    
    def sendDataToDataServer(self,payload):
        if self.data_server_host == '' or self.data_server_port == None:
            return False
        
        tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tcp_client.connect((self.data_server_host, self.data_server_port))
            tcp_client.send(payload)
            tcp_client.close()
        except:
            logging.warning('Error:sendDataToDataServer')
            return
    
    def setDataServerInfo(self,host,port):
        self.data_server_host = host
        self.data_server_port = port
        
#     def is_hex(s):
#         hex_digits = set("0123456789abcdefABCDEF")
#         for char in s:
#             if not (char in hex_digits):
#                 return False
#         return True

CONTAINER = 'WIZnet'
SUBS_PREFIX = 'wiznet_'
    
    
if __name__ == '__main__':
    thingplug = ThingPlug('onem2m.sktiot.com',9000)
    
    thingplug.login('daniel', 'wiznet1206^')
    thingplug.getDeviceList()

# Sample 
#     for i in range(20):
#         subs_name = 'subscription_%02d'%(i)
#         #print subs_name
#         if thingplug.isExistedSubscription(NODE_ID, subs_name, CONTAINER) == True:
#             thingplug.deleteSubscription(NODE_ID, subs_name, CONTAINER)
        
    mqtt_client_id = thingplug.getUserId() + "_bridge"
    thingplug.setMqttClientId(mqtt_client_id)
    thingplug.mqttConnect()

    thingplug.setDataServerInfo('222.98.173.202', 5000)
    #thingplug.setDataServerInfo('222.98.173.194', 5000)
    status,node_cnt,node_list = thingplug.getDeviceList()
    
    for i in range(int(node_cnt)):
        subs_name = SUBS_PREFIX + node_list[i]
        if thingplug.retrieveSubscription(node_list[i], subs_name, CONTAINER) == True:
            thingplug.deleteSubscription(node_list[i], subs_name, CONTAINER)
         
        thingplug.createSubscription(node_list[i], subs_name, CONTAINER, mqtt_client_id)
    
    thingplug.mqttLoopForever()
    
