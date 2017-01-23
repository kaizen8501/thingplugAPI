from ThingPlugApi import ThingPlug
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'ThingPlug Login Example')
    
    parser.add_argument('-u', '--user_id', type=str, help='ThingPlug User ID', required=True)
    parser.add_argument('-p', '--user_pw', type=str, help='ThingPlug User Password', required=True)
    
    args = parser.parse_args()
    
    thingplug = ThingPlug.ThingPlug('onem2m.sktiot.com',9000)
    thingplug.login(args.user_id, args.user_pw)
    print thingplug.getuKey()
