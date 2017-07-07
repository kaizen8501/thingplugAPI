import sys
import argparse
import time, datetime, sched
from sched import scheduler
sys.path.insert(0,'../')
import logging
from ThingPlugApi import ThingPlug 


THINGPLUG_HOST = 'onem2m.sktiot.com'
THINGPLUG_PORT = 9443
PERIOD_TIME = 0

def fun_getLatestData(thingplug,node_id, container, enable_log):
    try:
        status, data, lt_time = thingplug.getLatestData(node_id,container)
        current_time = str(datetime.datetime.now())
        output_data = current_time + ',' + data + ',' + lt_time + '\r\n'
        print output_data,
        
        if enable_log > 0:
            f = open('get_latest_data.log','a')
            f.write(output_data)
            f.close()
    except:
        logging.warning('Fail fun_getLatestData')
        


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'ThingPlug Get Latest Data Example')
    
    parser.add_argument('-u', '--user_id', type=str, help='ThingPlug User ID', required=True)
    parser.add_argument('-p', '--user_pw', type=str, help='ThingPlug User Password', required=True)
    parser.add_argument('-ni', '--node_id', type=str, help='ThingPlug Node ID', required=True)
    parser.add_argument('-ct', '--container', type=str, help='ThingPlug Container Name', required=True)

    parser.add_argument('-ae', '--app_eui', type=str, help='ThingPlug APP EUI(Default:ThingPlug)', required=True)
    parser.add_argument('-th', '--thingplug_host', type=str, help='ThingPlug Host IP(Default:onem2m.sktiot.com)', required=False)
    parser.add_argument('-tp', '--thingplug_port', type=int, help='ThingPlug Port(Default:9443)', required=False)
    parser.add_argument('-pt', '--period_time', type=int, help='Get Latest Data Period Time(Default:0,One Time)', required=False)
    parser.add_argument('-el', '--enable_log', type=int, help='', required=False)
    
    args = parser.parse_args()
    

    if args.thingplug_host != None:    THINGPLUG_HOST = args.thingplug_host
    if args.thingplug_port != None:    THINGPLUG_PORT = args.thingplug_port
    if args.app_eui != None:           THINGPLUG_APPEUI = args.app_eui
    if args.period_time    != None:    PERIOD_TIME = args.period_time
    if args.enable_log     != None:    args.enable_log = 1
    
    
    thingplug = ThingPlug.ThingPlug(THINGPLUG_HOST,THINGPLUG_PORT)
    thingplug.login(args.user_id, args.user_pw)

    thingplug.setAppEui(args.app_eui)
    
    if PERIOD_TIME == 0:
        status, data, lt_time = thingplug.getLatestData(args.node_id, args.container)
        current_time = str(datetime.datetime.now())
        output_data = current_time + ',' + data + ',' + lt_time + '\r\n'
        print output_data,
    else:
        while True:
            scheduler = sched.scheduler(time.time, time.sleep)
            param = (thingplug, args.node_id, args.container, args.enable_log)
            scheduler.enter(PERIOD_TIME, 1, fun_getLatestData, param )
            scheduler.run()
        
