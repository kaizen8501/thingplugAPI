'''
Created on 2017. 4. 27.

@author: kaizen
'''
import sys
import argparse
import logging
import time, datetime
import socket
from bs4 import BeautifulSoup

sys.path.insert(0,'../')
from ThingPlugApi import ThingPlug 

THINGPLUG_HOST = 'onem2m.sktiot.com'
THINGPLUG_PORT = 9443
MQTT_CLIENT_ID = 'bridge'
SUBS_PREFIX = 'thingplug_'
CONTAINER = 'LoRa'

G_DATA_SERVER_HOST = "127.0.0.1"
G_DATA_SERVER_PORT = 5000
G_PAYLOAD_DECODE_OPT = 0


def sendDataToDataServer(payload):
    logging.info('Send data to ' + G_DATA_SERVER_HOST + "," + str(G_DATA_SERVER_PORT))
    tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        tcp_client.connect((G_DATA_SERVER_HOST, G_DATA_SERVER_PORT))
        tcp_client.send(payload)
        tcp_client.close()
    except:
        logging.warning('Error:sendDataToDataServer')
        return

def mqtt_on_message_cb(client, userdata, msg):
    # logging.info(msg.topic)
    # logging.info(msg.payload)
    try:
        xml_root = BeautifulSoup(msg.payload,'html.parser')
        device_name = getattr(xml_root.find('fr'),'string', None)
        data_payload = getattr(xml_root.find('pc').find('cin').find('con'), 'string', None)
        lt_time = getattr(xml_root.find('pc').find('cin').find('lt'), 'string', None)
    
        current_time = str(datetime.datetime.now())
        output_data = current_time + ',' + device_name + ',' + data_payload + ',' + lt_time
        logging.info(output_data)

        if G_PAYLOAD_DECODE_OPT == 0:
            payload = data_payload
        elif G_PAYLOAD_DECODE_OPT == 1:
            payload = data_payload.decode('hex')
        elif G_PAYLOAD_DECODE_OPT == 2:
            payload = data_payload.decode('hex').decode('hex')
        
        logging.info(payload)
        sendDataToDataServer(payload)
    except:
        logging.warning(data_payload)
        return
    
    if enable_log > 0:
        f = open('subscription_mqtt.log','a')
        f.write(output_data)
        f.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'ThingPlug Subscription(MQTT) Example')
    
    parser.add_argument('-u', '--user_id', type=str, help='ThingPlug User ID', required=True)
    parser.add_argument('-p', '--user_pw', type=str, help='ThingPlug User Password', required=True)
    parser.add_argument('-ae', '--app_eui', type=str, help='ThingPlug APP EUI', required=True)
    parser.add_argument('-dsh', '--bridge_ds_host', type=str, help='ThingPlug Bridge Data Server Host IP', required=True)
    parser.add_argument('-dsp', '--bridge_ds_port', type=int, help='ThingPlug Bridge Data Server Port', required=True)

    parser.add_argument('-ni', '--node_id', type=str, help='ThingPlug Node ID', required=False)
    parser.add_argument('-ct', '--container', type=str, help='ThingPlug Container Name(Default:LoRa)', required=False)
    parser.add_argument('-th', '--thingplug_host', type=str, help='ThingPlug Host IP(Default:onem2m.sktiot.com)', required=False)
    parser.add_argument('-tp', '--thingplug_port', type=int, help='ThingPlug Port(Default:9443)', required=False)
    parser.add_argument('-ci', '--mqtt_client_id', type=str, help='ThingPlug MQTT Client ID(Deafult:bridge)', required=False)
    parser.add_argument('-el', '--enable_log', type=int, help='', required=False)
    parser.add_argument('-pd', '--payload_decode_opt', type = int, help='ThingPlug Bridge Payload Decode Option(Default:0, 0:Bypass,1:1time decode,2:2time decode)', required=False)
    
    args = parser.parse_args()
    
    if args.container      != None:    CONTAINER = args.container
    if args.thingplug_host != None:    THINGPLUG_HOST = args.thingplug_host
    if args.thingplug_port != None:    THINGPLUG_PORT = args.thingplug_port
    if args.mqtt_client_id != None:    MQTT_CLIENT_ID = args.mqtt_client_id
    
    if args.bridge_ds_host != None:    G_DATA_SERVER_HOST = args.bridge_ds_host
    if args.bridge_ds_port != None:    G_DATA_SERVER_PORT = args.bridge_ds_port
    if args.payload_decode_opt != None: G_PAYLOAD_DECODE_OPT = args.payload_decode_opt

    global enable_log
    enable_log = 0
    if args.enable_log     != None:    enable_log = 1
        
    
    thingplug = ThingPlug.ThingPlug(THINGPLUG_HOST,THINGPLUG_PORT)
    logging.info('ThingPlug Login')
    thingplug.login(args.user_id, args.user_pw)
    
    thingplug.setAppEui(args.app_eui)
    #thingplug.getDeviceList()

    mqtt_client_id = thingplug.getUserId() + '_' + MQTT_CLIENT_ID 
    thingplug.setMqttClientId(mqtt_client_id)
    logging.info('MQTT Connect')    
    thingplug.mqttConnect()
    thingplug.mqttSetOnMessage(mqtt_on_message_cb)
    
    if args.node_id == None:
        logging.info('Get Device List')
        status,node_cnt,node_list = thingplug.getDeviceList()
    
        if node_cnt == None:
            logging.warning('Node list is empty')
            sys.exit()
    
        for i in range(int(node_cnt)):
            subs_name = SUBS_PREFIX + node_list[i]
            logging.info('Retrieve Subscription')
            if thingplug.retrieveSubscription(node_list[i], subs_name, CONTAINER) == True:
                logging.info('Delete Subscription')
                thingplug.deleteSubscription(node_list[i], subs_name, CONTAINER)
             
            logging.info('Create Subscription')
            thingplug.createSubscription(node_list[i], subs_name, CONTAINER, mqtt_client_id)
    else:
        subs_name = SUBS_PREFIX + args.node_id
        logging.info('Retrieve Subscription')
        if thingplug.retrieveSubscription(args.node_id, subs_name, CONTAINER) == True:
            logging.info('Delete Subscription')
            thingplug.deleteSubscription(args.node_id, subs_name, CONTAINER)
        
        logging.info('Create Subscription')
        thingplug.createSubscription(args.node_id, subs_name, CONTAINER, mqtt_client_id)
    
    thingplug.mqttLoopForever()
