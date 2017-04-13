import sys
import time
sys.path.append("../")
from ThingPlugApi import ThingPlug
import argparse

THINGPLUG_HOST = 'onem2m.sktiot.com'
THINGPLUG_PORT = 9443
THINGPLUG_APPEUI = 'ThingPlug'

g_tp_mgmtCmd_list_default = ['DevReset', 'extDevMgmt', 'RepImmediate', 'RepPerChange']

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ThingPlug mgmtCmd Example')

    parser.add_argument('-u', '--user_id', type=str, help='ThingPlug User ID', required=True)
    parser.add_argument('-p', '--user_pw', type=str, help='ThingPlug User Password', required=True)

    parser.add_argument('-th', '--thingplug_host', type=str, help='ThingPlug Host IP(Default:onem2m.sktiot.com)', required=False)
    parser.add_argument('-tp', '--thingplug_port', type=int, help='ThingPlug Port(Default:9443)', required=False)
    parser.add_argument('-ae', '--app_eui', type=str, help='ThingPlug APP EUI(Default:ThingPlug)', required=False)
    parser.add_argument('-n', '--node_id', type=str, help='ThingPlug Node ID', required=True)
    parser.add_argument('-cmt', '--command_type', type=str, help='ThingPlug Command Type. (DevReset, extDevMgmt, RepImmediate, RepPerChange)', required=True)
    parser.add_argument('-exra', '--request_argument', type=str, help='ThingPlug Excute Request Argument', required=False)

    args = parser.parse_args()
    exra = ''

    if args.thingplug_host != None:     THINGPLUG_HOST = args.thingplug_host
    if args.thingplug_port != None:     THINGPLUG_PORT = args.thingplug_port
    if args.app_eui != None:           THINGPLUG_APPEUI = args.app_eui
    if args.request_argument != None:   exra = args.request_argument

    thingplug = ThingPlug.ThingPlug(THINGPLUG_HOST, THINGPLUG_PORT)
    thingplug.login(args.user_id, args.user_pw)
    thingplug.setAppEui(THINGPLUG_APPEUI)

    ret, cmd_inst = thingplug.createMgmtInstance(args.node_id, args.command_type, exra)

    time.sleep(3)
    print thingplug.retrieveMgmtResult(args.node_id, args.command_type, cmd_inst)

