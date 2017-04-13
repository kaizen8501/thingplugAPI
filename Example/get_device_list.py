import sys
import argparse
sys.path.insert(0,'../')
from ThingPlugApi import ThingPlug 

THINGPLUG_HOST = 'onem2m.sktiot.com'
THINGPLUG_PORT = 9443
THINGPLUG_APPEUI = 'ThingPlug'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'ThingPlug Login Example')
    
    parser.add_argument('-u', '--user_id', type=str, help='ThingPlug User ID', required=True)
    parser.add_argument('-p', '--user_pw', type=str, help='ThingPlug User Password', required=True)
    parser.add_argument('-th', '--thingplug_host', type=str, help='ThingPlug Host IP(Default:onem2m.sktiot.com)', required=False)
    parser.add_argument('-tp', '--thingplug_port', type=int, help='ThingPlug Port(Default:9443)', required=False)
    parser.add_argument('-ae', '--app_eui', type=str, help='ThingPlug APP EUI(Default:ThingPlug)', required=False)

    args = parser.parse_args()

    if args.thingplug_host != None:    THINGPLUG_HOST = args.thingplug_host
    if args.thingplug_port != None:    THINGPLUG_PORT = args.thingplug_port
    if args.app_eui != None:           THINGPLUG_APPEUI = args.app_eui

    thingplug = ThingPlug.ThingPlug(THINGPLUG_HOST,THINGPLUG_PORT)
    thingplug.login(args.user_id, args.user_pw)

    thingplug.setAppEui(THINGPLUG_APPEUI)

    print thingplug.getDeviceList() # Return ( True/False, device_cnt, device_list )