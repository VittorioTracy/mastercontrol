#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This agent uses the python-openzwave library to connect to a USB Zwave controller and replicates Zwave events into MCP and vice versa.
"""

from lib.event import event
from lib.timetools import howlongago

from libopenzwave import PyManager, PyOptions
from time import time
from logging import getLogger
from yaml import dump

# Global Variables
logger = getLogger(__name__)

# FIXME: These are command definitions that enable sending events, commands through XMPP for example, and making things happen in the Zwave network, such as turning lights on or off. These commands below are specific to certain nodes in my Zwave network so for them to work on a nother network the commands will need to be modified. These should be moved to a file that contains user logic.
COMMANDS = { 
             'porch'     :  { 'on'           : { 'description'  : 'Turn the porch light on',
                                                 'authorized'   : 'ALL',
                                                 'handlerevent' : { 'id': 'openzwave', 'event': 'setValue',
                                                                    'data': { 'node': 'RGB Light - Porch', 'name': 'Level', 'value': 99 }}},
                              'half'         : { 'description'  : 'Turn the porch light to half',
                                                 'authorized'   : 'ALL',
                                                 'handlerevent' : { 'id': 'openzwave', 'event': 'setValue',
                                                                    'data': { 'node': 'RGB Light - Porch', 'name': 'Level', 'value': 50 }}},
                              'off'          : { 'description'  : 'Turn the porch light off',
                                                 'authorized'   : 'ALL',
                                                 'handlerevent' : { 'id': 'openzwave', 'event': 'setValue',
                                                                    'data': { 'node': 'RGB Light - Porch', 'name': 'Level', 'value': 0 }}},
                              'white'        : { 'description'  : 'Set the porch light color to white',
                                                 'authorized'   : 'ALL',
                                                 'handlerevent' : { 'id': 'openzwave', 'event': 'setValue',
                                                                    'data': { 'node': 'RGB Light - Porch', 'name': 'Color Index', 'value': 'Cool White' }}},
                              'red'          : { 'description'  : 'Set the porch light color to red',
                                                 'authorized'   : 'ALL',
                                                 'handlerevent' : { 'id': 'openzwave', 'event': 'setValue',
                                                                    'data': { 'node': 'RGB Light - Porch', 'name': 'Color Index', 'value': 'Red' }}},
                              'lime'         : { 'description'  : 'Set the porch light color to lime green',
                                                 'authorized'   : 'ALL',
                                                 'handlerevent' : { 'id': 'openzwave', 'event': 'setValue',
                                                                    'data': { 'node': 'RGB Light - Porch', 'name': 'Color Index', 'value': 'Lime' }}},
                              'blue'         : { 'description'  : 'Set the porch light color to blue',
                                                 'authorized'   : 'ALL',
                                                 'handlerevent' : { 'id': 'openzwave', 'event': 'setValue',
                                                                    'data': { 'node': 'RGB Light - Porch', 'name': 'Color Index', 'value': 'Blue' }}},
                              'yellow'       : { 'description'  : 'Set the porch light color to yellow',
                                                 'authorized'   : 'ALL',
                                                 'handlerevent' : { 'id': 'openzwave', 'event': 'setValue',
                                                                    'data': { 'node': 'RGB Light - Porch', 'name': 'Color Index', 'value': 'Yellow' }}},
                              'cyan'         : { 'description'  : 'Set the porch light color to cyan',
                                                 'authorized'   : 'ALL',
                                                 'handlerevent' : { 'id': 'openzwave', 'event': 'setValue',
                                                                    'data': { 'node': 'RGB Light - Porch', 'name': 'Color Index', 'value': 'Cyan' }}},
                              'green'        : { 'description'  : 'Set the porch light color to green',
                                                 'authorized'   : 'ALL',
                                                 'handlerevent' : { 'id': 'openzwave', 'event': 'setValue',
                                                                    'data': { 'node': 'RGB Light - Porch', 'name': 'Color Index', 'value': 'Green' }}},
                              'purple'       : { 'description'  : 'Set the porch light color to purple',
                                                 'authorized'   : 'ALL',
                                                 'handlerevent' : { 'id': 'openzwave', 'event': 'setValue',
                                                                    'data': { 'node': 'RGB Light - Porch', 'name': 'Color Index', 'value': 'Purple' }}},
                              'teal'        : { 'description'  : 'Set the porch light color to teal',
                                                 'authorized'   : 'ALL',
                                                 'handlerevent' : { 'id': 'openzwave', 'event': 'setValue',
                                                                    'data': { 'node': 'RGB Light - Porch', 'name': 'Color Index', 'value': 'Teal' }}},
                              'cwoff'        : { 'description'  : 'Set the porch light cold white to off',
                                                 'authorized'   : 'ALL',
                                                 'handlerevent' : { 'id': 'openzwave', 'event': 'setValue',
                                                                    'data': { 'node': 'RGB Light - Porch', 'name': 'Color', 'value': '#0000000000' }}},
                              'cwon'         : { 'description'  : 'Set the porch light cold white to on',
                                                 'authorized'   : 'ALL',
                                                 'handlerevent' : { 'id': 'openzwave', 'event': 'setValue',
                                                                    'data': { 'node': 'RGB Light - Porch', 'name': 'Color', 'value': '#00000000FF' }}},
                              'red2'         : { 'description'  : 'Set the porch light cold white to red',
                                                 'authorized'   : 'ALL',
                                                 'handlerevent' : { 'id': 'openzwave', 'event': 'setValue',
                                                                    'data': { 'node': 'RGB Light - Porch', 'name': 'Color', 'value': '#FF00000000' }}},
                              'getconfig'    : { 'description'  : 'Get node config',
                                                 'authorized'   : 'ALL',
                                                 'handlerevent' : { 'id': 'openzwave', 'event': 'requestAllConfigParams',
                                                                    'data': { 'nodeid': 4 }}},
                                                                    #'data': { 'node': 'RGB Light - Porch' }}},
                              'getstats'     : { 'description'  : 'Get node statistics',
                                                 'authorized'   : 'ALL',
                                                 'handlerevent' : { 'id': 'openzwave', 'event': 'getNodeStatistics',
                                                                    'data': { 'nodeid': 4 }}},
                              #                                      #'data': { 'node': 'RGB Light - Porch' }}},
                              'isawake'     : { 'description'  : 'Check if awake',
                                                'authorized'   : 'ALL',
                                                'handlerevent' : { 'id': 'openzwave', 'event': 'isNodeAwake',
                                                                    'data': { 'nodeid': 4 }}},
                                                                   #'data': { 'node': 'Dimmer - Livingroom' }}},
                              'isfailed'    : { 'description'  : 'Check if failed',
                                                'authorized'   : 'ALL',
                                                'handlerevent' : { 'id': 'openzwave', 'event': 'isNodeFailed',
                                                                    'data': { 'nodeid': 4 }}},
                                                                   #'data': { 'node': 'Dimmer - Livingroom' }}},
                            },           
             'livingroom' : { 'on'          : { 'description'  : 'Turn the livingroom light on',
                                                'authorized'   : 'ALL',
                                                'handlerevent' : { 'id': 'openzwave', 'event': 'setValue',
                                                                    'data': { 'node': 'Dimmer - Livingroom', 'name': 'Level', 'value': 99 }}},
                             'off'          : { 'description'  : 'Turn the livingroom light off',
                                                'authorized'   : 'ALL',
                                                'handlerevent' : { 'id': 'openzwave', 'event': 'setValue',
                                                                   'data': { 'node': 'Dimmer - Livingroom', 'name': 'Level', 'value': 0 }}},
                             'dim'          : { 'description'  : 'Turn the livingroom light to 20%',
                                                'authorized'   : 'ALL',
                                                'handlerevent' : { 'id': 'openzwave', 'event': 'setValue',
                                                                   'data': { 'node': 'Dimmer - Livingroom', 'name': 'Level', 'value': 20 }}},
                             'half'         : { 'description'  : 'Turn the livingroom light to 50%',
                                                'authorized'   : 'ALL',
                                                'handlerevent' : { 'id': 'openzwave', 'event': 'setValue',
                                                                   'data': { 'node': 'Dimmer - Livingroom', 'name': 'Level', 'value': 50 }}},
                              'getconfig'   : { 'description'  : 'Get node config',
                                                'authorized'   : 'ALL',
                                                'handlerevent' : { 'id': 'openzwave', 'event': 'requestAllConfigParams',
                                                                    'data': { 'nodeid': 8 }}},
                                                                   #'data': { 'node': 'Dimmer - Livingroom' }}},
                              'getstats'    : { 'description'  : 'Get node statistics',
                                                'authorized'   : 'ALL',
                                                'handlerevent' : { 'id': 'openzwave', 'event': 'getNodeStatistics',
                                                                    'data': { 'nodeid': 8 }}},
                                                                   #'data': { 'node': 'Dimmer - Livingroom' }}},
                              'isawake'     : { 'description'  : 'Check if awake',
                                                'authorized'   : 'ALL',
                                                'handlerevent' : { 'id': 'openzwave', 'event': 'isNodeAwake',
                                                                    'data': { 'nodeid': 8 }}},
                                                                   #'data': { 'node': 'Dimmer - Livingroom' }}},
                              'isfailed'    : { 'description'  : 'Check if failed',
                                                'authorized'   : 'ALL',
                                                'handlerevent' : { 'id': 'openzwave', 'event': 'isNodeFailed',
                                                                    'data': { 'nodeid': 8 }}},
                                                                   #'data': { 'node': 'Dimmer - Livingroom' }}},
                            },           
           }

class openzwave:
    def __init__(self, config, state, eventcallback):
        self.nodes = config['nodes'] 
        self.byname = dict()
        self.config = config
        self.receiver = eventcallback

        zopts = { 'user_path': '.', 'cmd_line': '--logging false' }
        if self.config.has_key('config_path'):
            zopts['config_path'] = self.config['config_path']

        options = PyOptions(**zopts)
        options.lock()
        self.manager = PyManager()
        self.manager.create()
        logger.debug('Startup: Add watcher')
        self.manager.addWatcher(self.callback)
        logger.debug('Startup: Add device')
        self.manager.addDriver(self.config['device'])
        logger.info('Startup Complete')
        # subscribe to shutdown event
        eventcallback(event('shutdown', '', 'subscribe', 'shutdown'))
        eventcallback(event('openzwave', '', 'subscribe', 'ALL'))
        eventcallback(event(**{'id': 'command-add', 'type': 'command', 'data': { 'operation': 'add', 'command': COMMANDS }}))


    def shutdown(self):
        logger.debug('Shutdown: Remove watcher')
        self.manager.removeWatcher(self.callback)
        logger.debug('Shutdown: Remove device')
        self.manager.removeDriver(self.config['device'])
        logger.info('Shutdown Complete')


    def eventhandler(self, event):
        logger.debug("Eventhandler - event: %s", event.dump())
        if event.eventid() == 'shutdown':
            logger.debug("Got shutdown event")
            self.shutdown()
        elif event.eventid() == 'openzwave':
            logger.debug("Got openzwave event: %s", event.eventbody())
            data = event.eventdata()
            if event.eventbody() == 'healNetwork':
                self.manager.healNetwork(self.homeid, True)
                logger.info("healNetwork initiated")
            if event.eventbody() == 'getNodeName':
                name = self.manager.getNodeName(self.homeid, data['nodeid'])
                logger.debug("getNodeName node id '%i' name is '%s'", data['nodeid'], name)
            if event.eventbody() == 'setNodeName':
                self.manager.setNodeName(self.homeid, data['nodeid'], data['name'])
                logger.debug("setNodeName setting node id '%i' name to '%s'", data['nodeid'], data['name'])
            if event.eventbody() == 'getNodeLocation':
                location = self.manager.getNodeLocation(self.homeid, data['nodeid'])
                logger.debug("getNodeLocation node id '%i' location is '%s'", data['nodeid'], location)
            if event.eventbody() == 'setNodeLocation':
                self.manager.setNodeLocation(self.homeid, data['nodeid'], data['location'])
                logger.debug("setNodeLocation setting node id '%i' location to '%s'", data['nodeid'], data['location'])
            if event.eventbody() == 'setNodeOn':
                self.manager.setNodeOn(self.homeid, data['nodeid'])
                logger.debug("setNodeOn turning on node id '%i'", data['nodeid'])
            if event.eventbody() == 'setNodeOff':
                self.manager.setNodeOff(self.homeid, data['nodeid'])
                logger.debug("setNodeOff turning off node id %i", data['nodeid'])
            if event.eventbody() == 'setValue':
                logger.debug("setValue node name '%s' = '%s'", data['node'], self.byname[data['node']])
                logger.debug("setValue '%s'", str(self.byname[data['node']]['bylabel'][data['name']]))
                self.manager.setValue(self.byname[data['node']]['bylabel'][data['name']]['id'], data['value'])
            if event.eventbody() == 'requestAllConfigParams': 
                logger.debug("Requesting All Config Params")
                self.manager.requestAllConfigParams(self.homeid, data['nodeid'])
            if event.eventbody() == 'getNodeStatistics': 
                logger.debug("Requesting Node Statistics")
                stats = self.manager.getNodeStatistics(self.homeid, data['nodeid'])
                logger.debug(dump(stats, default_flow_style=False))
            if event.eventbody() == 'isNodeAwake': 
                logger.debug("Requesting if node is awake")
                ret = self.manager.isNodeAwake(self.homeid, data['nodeid'])
                if ret: logger.debug("Node is Awake")
                else: logger.debug("Node is Not Awake")
            if event.eventbody() == 'isNodeFailed': 
                logger.debug("Requesting if node is failed")
                ret = self.manager.isNodeFailed(self.homeid, data['nodeid'])
                if ret: logger.debug("Node is Failed")
                else: logger.debug("Node is Not Failed")
        #elif event.eventtype() == 'message' and len(event.eventuser()):


    # convert C to F
    def convertCtoF(self, c):
        return "{0:.1f}".format(9.0/5.0 * c + 32)


    # callback order: (notificationtype, homeid, nodeid, ValueID, groupidx, event)
    # example args
    #    {'homeId': 25480663, 'valueId': {'index': 1, 'units': u'F', 'type': 'Decimal', 'nodeId': 2, 'value': 76.5, 'commandClass': 'COMMAND_CLASS_SENSOR_MULTILEVEL', 'instance': 1, 'readOnly': True, 'homeId': 25480663, 'label': u'Temperature', 'genre': 'User', 'id': 72057594076479506L}, 'notificationType': 'ValueChanged', 'nodeId': 2}
    def callback(self, args):
        msg = ''
        if not args:
            logger.warning('Callback args are undefined')
            return
        
        nodeid = args['nodeId']
        try: #if self.nodes.has_key(nodeid): 
            nodename = self.nodes[nodeid]['name']
            self.nodes[nodeid]['lastseen'] = time()
        except KeyError: 
            nodename = 'Node '+ str(nodeid)
            self.nodes[nodeid] = { 'name': nodename, 'lastseen': time() }
        try: self.nodes[nodeid]['values']
        except KeyError:
            self.nodes[nodeid]['values'] = dict()
        try: self.nodes[nodeid]['bylabel']
        except KeyError:
            self.nodes[nodeid]['bylabel'] = dict()
            
        if nodename not in self.byname:
            self.byname[nodename] = self.nodes[nodeid]

        msg = nodename + ': ' + str(args['notificationType'])
        if 'valueId' in args:
            v = args['valueId']
            #print('valueID: {}'.format(v['id']))
            if not self.nodes[nodeid]['values'].has_key(v['id']):
                self.nodes[nodeid]['values'][v['id']] = { 'id': v['id'] }  
            if v.has_key('label'):
                self.nodes[nodeid]['values'][v['id']]['label'] = v['label']
                msg += ' ' + v['label'] + ' ='
                if not self.nodes[nodeid]['bylabel'].has_key(v['label']):
                    self.nodes[nodeid]['bylabel'][v['label']] = self.nodes[nodeid]['values'][v['id']]  
            if v.has_key('value'):
                self.nodes[nodeid]['values'][v['id']]['value'] = v['value']
                if self.config['convertctof'] == True and v['units'].lower() == 'c':
                    v['value'] = self.convertCtoF(v['value']) 
                    self.nodes[nodeid]['values'][v['id']]['value'] = v['value']
                    v['units'] = 'F'
                msg += ' ' + str(v['value'])
            else: self.nodes[nodeid]['values'][v['id']]['value'] = ''
            try: 
                self.nodes[nodeid]['values'][v['id']]['units'] = v['units']
                msg += ' ' + str(v['units'])
            except KeyError: self.nodes[nodeid]['values'][v['id']]['units'] = ''
            if v.get('readOnly'):
                self.nodes[nodeid]['values'][v['id']]['readonly'] = True 
                msg += ' (ReadOnly)'
            else: 
                self.nodes[nodeid]['values'][v['id']]['readonly'] = False
            self.nodes[nodeid]['values'][v['id']]['updated'] = time()
     
        if args['notificationType'] == 'Notification': 
            msg += ' notificationCode = '+ str(args['notificationCode'])
        if args['notificationType'] == 'NodeEvent':
            msg += ' event = '+ str(args['event']) 
        if args['notificationType'] == 'Group':
            msg += ' groupIdx = '+ str(args['groupIdx'])
                
        # {'homeId': 25480663, 'notificationType': 'DriverReady', 'nodeId': 1}
        if args['notificationType'] == 'DriverReady' and args['nodeId'] == 1:
            self.homeid = args['homeId'] 
            logger.debug("DriverReady - homeId: %i", args['homeId'])
        self.receiver(event('openzwave', msg))

    def nodeList(self, args):
        nodeType = args['words'][0]
        return "Command nodeList type:", nodeType

    def getValue(self, args):
        node = args['words'][0]
        var = args['words'][1]
        msg = str()
        if len(args['words']) > 2: # set value
            # FIXME 
            msg = "Command getValue set", node, var, "=", args['words'][2]
        else:                      # get value
            if var == 'values':
                for eachvar in args['nodeinfo']['values'].keys():
                    msg += "\t{} = {}\n".format(eachvar, args['nodeinfo']['values'][eachvar])
            elif var in args['nodeinfo']['values'].keys():
                msg = "Command getValue get", node, var, "=", args['value'][var]
            else:
                msg = "Value not found for ", var
        return msg

    def setLight(self, args):
        return "Command setLight {}".format(args['words'][1])

    def setLock(self, args):
        state = args['words'][1]
        return "Command setLock {}".format(state)

    def getNode(self, node):
        if node.isdigit() and int(node) in NODES:
            logger.debug("Found node by node number!")
            return NODES[int(node)]
        for n in NODES.values():
            if (n['name'] == node):
                logger.debug("Found node by node name!")
                return n

    def zwavetest(self, args):
        logger.debug("Zwavetest args: {}".format(args))
        return "zwavetest command run"

    # dump status for a single node or several nodes
    def dumpnode(self, nodelist = list()):
        msg = str()
        for nodeid in NODES.keys():
            longago = howlongago(NODES[nodeid]['lastseen'])
            msg += "{} ID: {} Last: {}\n".format(NODES[nodeid]['name'], nodeid, longago)
            for valueid in NODES[nodeid]['values']:
               updated = 0
               if NODES[nodeid]['values'][valueid].has_key('updated'): updated = NODES[nodeid]['values'][valueid]['updated']
               else: break
               value = 'N/A'
               if NODES[nodeid]['values'][valueid].has_key('value'): value = NODES[nodeid]['values'][valueid]['value']
               label = 'N/A'
               if NODES[nodeid]['values'][valueid].has_key('label'): label = NODES[nodeid]['values'][valueid]['label']
               units = ''
               if NODES[nodeid]['values'][valueid].has_key('units'): units = NODES[nodeid]['values'][valueid]['units']

               msg += "\t{} = {} {}".format(label, value, units)
               if NODES[nodeid]['values'][valueid].has_key('readonly') and NODES[nodeid]['values'][valueid]['readonly']:
                  msg += ' (readonly)'
               msg += " Updated: {}".format(howlongago(updated))
               msg += "\n"

        #noalias_dumper = yaml.dumper.SafeDumper
        #noalias_dumper.ignore_aliases = lambda self, data: True
        #msg += "\n\nDUMP NODES\n"+ "\n"+ yaml.dump(NODES, default_flow_style=False, Dumper=noalias_dumper)
        return msg


### Main ###
#if __name__ == "__main__":
#signal.pause() # run until kill signal
