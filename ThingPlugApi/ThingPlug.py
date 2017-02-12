import sys
import httplib
import json
import random
import logging
import threading
import socket
import paho.mqtt.client as mqtt
#import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import argparse

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

class ThingPlug(object):
    def __init__(self,host,port):
        self.app_eui = ''
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
        
#         if len(self.app_eui) == 0:
#             logging.warning('Need to set APP EUI')
#             return False
        
        htt_header = {"password" : self.user_pw,
                      "user_id" : self.user_id,
                      "Accept": "application/json"
                      }
        
        self.http_connect()
        #query = "/" + self.app_eui + "?division=user&function=login"
        #self.conn.request("PUT",query, "", htt_header)
        self.conn.request("PUT","/ThingPlug?division=user&function=login", "", htt_header)
        resp_data = self.conn.getresponse()
        
        if resp_data.status != 200:
            logging.warning('status :' + str(resp_data.status))
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
            return False, None, None
        
        headers = {"uKey" : self.ukey,
                   "Accept": "application/json"
                   }

        query = "/ThingPlug?division=searchDevice&function=myDevice&startIndex=1&countPerPage=1"
        self.http_connect()
        self.conn.request("GET",query,"", headers)
        resp_data = self.conn.getresponse()
        
        if resp_data.status != 200:
            logging.warning('status :' + resp_data.status)
            self.http_close()
            return False, None, None

        json_body = json.loads(resp_data.read())
        if json_body['result_code'] != '200':
            logging.warning("getDeviceList Fail[result code : " + json_body['result_code'] + "]")
            self.http_close()
            return False, None, None

        self.deviceCnt = json_body['total_list_count']

        countPerPage = 10
        self.deviceList = []
        reqCnt = int(self.deviceCnt) / countPerPage
        idxCnt = countPerPage

        if( int(self.deviceCnt) % countPerPage != 0 ):  
            reqCnt += 1
            reminder = int(self.deviceCnt) % countPerPage
        else:
            reminder = 0
            
        for i in range(reqCnt):
            query = "/ThingPlug?division=searchDevice&function=myDevice&startIndex="
            query += str( (i*countPerPage) + 1)
            query += "&countPerPage="
            query += str(countPerPage)
 
            self.http_connect()
            self.conn.request("GET",query,"", headers)
            resp_data = self.conn.getresponse()
              
            if resp_data.status != 200:
                logging.warning('status :' + resp_data.status)
                self.http_close()
                return False, None, None
             
            json_body = json.loads(resp_data.read())
            if json_body['result_code'] != '200':
                logging.warning("getDeviceList Fail[result code : " + json_body['result_code'] + "]")
                self.http_close()
                return False, None, None

            if( (i==reqCnt -1) and reminder != 0 ):
                idxCnt = reminder

            for idx in range(0,idxCnt):
                try:
                    self.deviceList.append(json_body['deviceSearchAPIList'][idx]['device_Id'])
                    logging.info(json_body['deviceSearchAPIList'][idx]['device_Id'])
                except:
                    logging.warning('getDeviceList Fail[error idx : ' + str(idx) + "]")
                    pass
             
        self.http_close()
        return True, self.deviceCnt, self.deviceList

    def getLatestData(self,node_id,container):
        if len(self.app_eui) == 0:
            logging.warning('Need to set APP EUI')
            return False

        headers = {"Connection" : "keep-alive",
                   "uKey" : self.ukey,
                   "X-M2M-Origin" : node_id,
                   "X-M2M-RI" : node_id + "_" + str(random.randrange(1000,1100)),
                   "Accept": "application/json"
                   }
        
        #query = "/ThingPlug/v1_0/remoteCSE-"+ node_id + "/container-" + container + "/latest"
        query = "/" + self.app_eui + "/v1_0/remoteCSE-"+ node_id + "/container-" + container + "/latest"
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

        if len(self.app_eui) == 0:
            logging.warning('Need to set APP EUI')
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

        #query = '/ThingPlug/v1_0/remoteCSE-' + node_id + '/container-' + container_name
        query = '/' + self.app_eui + '/v1_0/remoteCSE-' + node_id + '/container-' + container_name
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
        
        if len(self.app_eui) == 0:
            logging.warning('Need to set APP EUI')
            return False

        headers = {"Accept": "application/json",
           "X-M2M-Origin" : node_id,
           "X-M2M-RI" : node_id + "_" + str(random.randrange(1000,1100)),
           "uKey" : self.ukey
           }
  
        #query = '/ThingPlug/v1_0/remoteCSE-' + node_id + '/container-' + container_name + '/subscription-' + subs_name
        query = '/' + self.app_eui + '/v1_0/remoteCSE-' + node_id + '/container-' + container_name + '/subscription-' + subs_name
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
        
        if len(self.app_eui) == 0:
            logging.warning('Need to set APP EUI')
            return False        

        headers = {
            'accept': "application/json",
            'x-m2m-ri': node_id + "_" + str(random.randrange(1000,1100)),
            'x-m2m-origin': node_id,
            'ukey': self.ukey,
            'content-type': "application/vnd.onem2m-res+xml;ty=23",
            }
        
        #query = "/ThingPlug/v1_0/remoteCSE-" + node_id + "/container-" + container_name + "/subscription-" + subs_name
        query = "/" + self.app_eui + "/v1_0/remoteCSE-" + node_id + "/container-" + container_name + "/subscription-" + subs_name
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
            #data = data_payload.decode('hex')
            data = data_payload.decode('hex').decode('hex')
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
    
    def setAppEui(self,app_eui):
        self.app_eui = app_eui
        
#     def is_hex(s):
#         hex_digits = set("0123456789abcdefABCDEF")
#         for char in s:
#             if not (char in hex_digits):
#                 return False
#         return True

USER_ID = ""
USER_PW = ""

TP_HOST = "onem2m.sktiot.com"
TP_PORT = 9000

LK_HOST = "127.0.0.1"
LK_PORT = 5000

CONTAINER = 'LoRa'
APP_EUI = 'ThingPlug'
SUBS_PREFIX = 'wiznet_'
    
#Parameter -h onem2m.sktiot.com -u lk_technet -pw lktn34!!@@ -p 9000 -lh 127.0.0.1 -lp 5000


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = '')
    
    parser.add_argument('-u', '--user_id', type=str, help='ThingPlug User ID', required=True)
    parser.add_argument('-pw', '--user_pw', type=str, help='ThingPlug User Password', required=True)
    
    parser.add_argument('-th', '--tp_host', type=str, help='ThingPlug Host', required=False)
    parser.add_argument('-tp', '--tp_port', type=int, help='ThingPlug Port', required=False)

    parser.add_argument('-lh', '--lk_host', type=str, help='LK Technet Host', required=False)
    parser.add_argument('-lp', '--lk_port', type=int, help='LK Technet Port', required=False)
    
    parser.add_argument('-c', '--container', type=str, help='ThingPlug Container Name', required=False)
    parser.add_argument('-ae', '--app_eui', type=str, help='ThingPlug App EUI', required=False)
    
    args = parser.parse_args()

    USER_ID = args.user_id
    USER_PW = args.user_pw

    if args.tp_host != None:    TP_HOST = args.tp_host
    if args.tp_port != None:    TP_PORT = args.tp_port
    if args.lk_host != None:    LK_HOST = args.lk_host
    if args.lk_port != None:    LK_PORT = args.lk_port
    if args.container != None:  CONTAINER = args.container
    if args.app_eui != None:    APP_EUI = args.app_eui
    
    thingplug = ThingPlug(TP_HOST,TP_PORT)
    
    thingplug.setAppEui(APP_EUI)
    thingplug.login(USER_ID, USER_PW)
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

    thingplug.setDataServerInfo(LK_HOST, LK_PORT)
    status,node_cnt,node_list = thingplug.getDeviceList()
    
    if node_cnt == None:
        logging.warning('Node list is empty')
        sys.exit()
    
    for i in range(int(node_cnt)):
        subs_name = SUBS_PREFIX + node_list[i]
        if thingplug.retrieveSubscription(node_list[i], subs_name, CONTAINER) == True:
            thingplug.deleteSubscription(node_list[i], subs_name, CONTAINER)
         
        thingplug.createSubscription(node_list[i], subs_name, CONTAINER, mqtt_client_id)
    
    thingplug.mqttLoopForever()
    
