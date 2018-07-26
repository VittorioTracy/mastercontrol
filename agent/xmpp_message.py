#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This agent connects to a XMPP instant messaging server and translates messages to MCP events and vice versa.
"""
import xmpp
import time
import sys
import logging

from lib.event import event

logger = logging.getLogger(__name__)

class xmpp_message:
    def __init__(self, config, state, eventcallback):
        # create xmpp client
        self.client = xmpp.Client(config['domain'])
        # id, event = '', type = 'message', agent = '', user = ''
        # subscribe to shutdown event
        eventcallback(event('shutdown', '', 'subscribe', 'shutdown'))
        # subscribe to xmpp_message events
        eventcallback(event('xmpp_message', '', 'subscribe', 'ALL'))
        # turn on timestamps in the log
        self.client._DEBUG.time_stamp = 1
        # open logfile
        if config.has_key('logfile') and len(config['logfile']):
            try:
                self.client._DEBUG._fh = open(config['logfile'],'w')
            except:
                logger.critical('Cannot open {} for writing'.format(config['logfile']))
                sys.exit(0)
        # ...connect it to SSL port directly
        port = 5222
        if config.has_key('port'): port = config['port']
        if not self.client.connect(server = (config['server'], port)):
            raise IOError('Can not connect to server.')
        # ...authorize client
        if not self.client.auth(config['user'], config['password'], config['server']):
            raise IOError('Can not auth with server.')
        self.client.sendInitPresence()
        # ...work some time
        self.client.Process(1)
        # register xmpp messsage handler
        self.daemonize = False 
        self.receiver = eventcallback 
        self.client.RegisterHandler('message', self.receive)
        self.daemonizeit()

    def shutdown(self):
        logger.debug("Shutdown called")
        self.daemonize = False 
        if self.client.isConnected(): self.client.disconnect()
        time.sleep(2)
        logger.info("Shutdown complete")

    def eventhandler(self, event):
        logger.debug("Eventhandler - event: %s", event.dump())
        if event.eventid() == 'shutdown':
            logger.debug("Got shutdown event")
            self.shutdown()
        elif event.eventtype() == 'message' and len(event.eventuser()):
            logger.debug("Got user message event for: %s", event.eventuser())
            # TODO: check user against roster
            self.send(event.eventuser(), event.eventbody()) 

    def send(self,contact, message):
        if not self.client.isConnected(): self.client.reconnectAndReauth()
        # ...send an ASCII message
        self.client.send(xmpp.Message(contact, message))
        self.client.Process(1)

    def receive(self, con, xmppevent):
        type = xmppevent.getType()
        from_id = xmppevent.getFrom().getStripped()
        if type in ['message', 'chat', None]:
            if xmppevent.getBody():
                #print from_id+':', event.getBody()
                ce = event(**{'id': 'command-{}'.format(from_id), 'event': xmppevent.getBody(), 'type': 'command', 'user': from_id, 'data': { 'returnid': 'xmpp_message' }})
                #self.receiver(event(from_id, event.getBody()))
                self.receiver(ce)

    def process(self):
        logger.debug("Starting processing")
        while self.daemonize:
            self.client.Process(1)
            #time.sleep(2)
        logger.debug("Stopping processing")

    def daemonizeit(self):
        if self.daemonize: return
        import threading
        
        self.daemonize = True
        d = threading.Thread(name='process', target=self.process)
        d.setDaemon(False)
        d.start()


### Main ###


if __name__ == "__main__":
    import sys, time
    logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s: %(message)s', 
                        datefmt='%Y/%m/%d-%H:%M:%S', level=logging.DEBUG)
    print_usage = False   

    sys.argv.pop(0) # remove program name from arg list
    for arg in sys.argv:
        if arg.startswith("--server"):
            temp,server = arg.split("=")
        elif arg.startswith("--domain"):
            temp, domain = arg.split("=")
        elif arg.startswith("--user"):
            temp,user = arg.split("=")
        elif arg.startswith("--password"):
            temp,password = arg.split("=")
        elif arg.startswith("--contact"):
            temp,contact = arg.split("=")
        elif arg.startswith("--message"):
            temp,message = arg.split("=")
        else:
            print_usage = True

    if not sys.argv or print_usage:
        print("Usage : ")
        print("  --server={XMPP server}")
        print("  --domain={XMPP domain}")
        print("  --user={XMPP user}")
        print("  --password={XMPP user password}")
        print("  --contact={XMPP contact}")
        print("  --message={message}")
        exit(1)

    def test_receiver(event):
        logger.debug('Received message: %s', event.eventbody())

    #FIXME: add input checks
    xm = xmpp_message({'server': server, 'domain': domain, 'user': user, 'password': password}, {}, test_receiver)
    xm.send(contact, message)
    time.sleep(30)
    xm.shutdown()


