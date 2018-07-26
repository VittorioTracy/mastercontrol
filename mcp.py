#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Master Control, Master Control Progra, or MCP, is a multi-threaded and event driven platform for managing and integrating various agent modules.
Agents provide functionality and communicate by emitting and receiving events.

See the README.md file for more information.

Basic duties:
    Manage agents.
    Manage event subscriptions.
    Receive events from agents.
    Dispatch events to subscribers.
"""
import sys, os
import signal
from time import sleep
import yaml
import importlib
from Queue import Queue
from threading import Thread, active_count, currentThread
import logging

# core modules
from lib.command import command
#import lib.authorize
#import lib.logic
from lib.schedule import schedule
#import lib.storage
from lib.event import event

# Global Variables
CONFIG = dict()
WORKERNUM = 2 

"""
    Main mastercontrol program class
"""
class mcp:
    def __init__(self):
        logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s: %(message)s', datefmt='%Y/%m/%d-%H:%M:%S', level=logging.DEBUG)
        # Catch signals and send to signal_handler
        signal.signal(signal.SIGHUP, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        #FIXME add try fail on config load
        with open('etc/mcp.conf', 'r') as confile:
            global CONFIG    
            CONFIG = yaml.load(confile)

        self.state = dict()
        self.state['agent'] = dict()
        #self.storage = lib.storage(CONFIG['storage'], self.state)
        self.eventqueue = Queue()
        self.subscription = dict()
        self.command = command(self.queueevent) # TODO: config?
        #self.command = command(self.queueevent, CONFIG)
        self.scheduler = schedule(self.queueevent, CONFIG)
        self.loadagents()
        #TODO: return agent load result

        # Create queue worker threads
        for i in range(WORKERNUM):
            t = Thread(target=self.dispatch)
            t.daemon = True 
            t.start()


    def shutdown(self):
        logging.info("Shutdown started - Queue size: %i", self.eventqueue.qsize())
        #res = self.storage.store()
        self.scheduler.removeall()
        # send shutdown event to all agents
        self.eventqueue.put(event('shutdown'))
        self.eventqueue.join()
        logging.info("Shutdown complete")

    def signal_handler(self, signum, frame):
        signame = { 1: 'SIGHUP', 2: 'SIGINT', 15: 'SIGTERM' }
        logging.info('Signal recieved: '+ signame[signum])
        self.shutdown()
        sys.exit(0)  

    """ Load enabled agents. 
        On load we pass a dictionary with the agent config, agent state, and a callback for agent events.
        On load agents return a load result and a callback to receive events (optional).
        Agents subscribe to events by sending specific subscribe/unsubscribe events. """
    def loadagents(self):
        self.agent = dict()
        logging.info("Loading Agents")
        for agent in CONFIG['agent'].keys():
            if CONFIG['agent'][agent].has_key('enabled') and CONFIG['agent'][agent]['enabled'] == True:
                pass
            else:
                logging.info("%s - disabled, skipping", agent)
                continue

            logging.info("%s - importing", 'agent.'+ agent)
            amod = importlib.import_module('agent.'+ agent)
            logging.info("%s - imported", agent)
            
            if not self.state['agent'].has_key(agent): self.state['agent'][agent] = dict()
            self.agent['agent.'+ agent] = getattr(amod, agent)(CONFIG['agent'][agent], self.state['agent'][agent], self.queueevent)
            logging.info("%s - instance created", agent)
            
    """ Events are queued by this function, and then processed by the dispatch thread. 
        Used as a callback by agents that emit events. 
    """
    def queueevent(self, event):
        #logging.debug("Queueevent - event: %s", event.dump()) 
        #TODO: check permissions
        self.eventqueue.put(event)

    """ Loop, processing queued events, dispatching events to subscribers.
        Special event ids:
            subscribe - subscribe to an event
            unsubscribe - unsubscribe from an event
            shutdown - receive notification of system shutdown
            all - match all events
    """
    def dispatch(self):
        logging.debug("Dispatch starting - Queue size: %i", self.eventqueue.qsize())
      
        while True:
            e = self.eventqueue.get()
            #logging.debug("Dispatch task started - thread: %s", currentThread().getName())
            if e.eventtype() == 'subscribe':
                self.subscribe(e)
                logging.debug("Dispatch subscribe done")
            elif e.eventtype() == 'unsubscribe':
                self.unsubscribe(e)
                logging.debug("Dispatch unsubscribe done")
            elif e.eventtype() == 'command':
                self.command.event(e)
                logging.debug("Dispatch command handler called for event: {}".format(e.dump()))
            else:
                logging.debug("Dispatch calling hanlder for event: {}".format(e.dump()))
           
                for subscriber, handler in self.subscribers(e).iteritems():
                    logging.debug("Dispatch calling handler for subscirber: %s", subscriber)
                    handler(e)
                    logging.debug("Dispatch handler done")
            self.eventqueue.task_done()
            #logging.debug("Dispatch task done - thread: %s queue size: %i", currentThread().getName(), self.eventqueue.qsize())
        logging.warning("XXXXXXXXX Dispatch done - Queue size: %i", self.eventqueue.qsize())

    """ Process subscribe events """
    def subscribe(self, event):
        logging.debug("Subscribe - event: %s", event.dump())
        if not self.subscription.has_key(event.eventagent()):
            self.subscription[event.eventagent()] = dict()
        if not self.subscription[event.eventagent()].has_key(event.eventid()):
            self.subscription[event.eventagent()][event.eventid()] = dict()
        self.subscription[event.eventagent()][event.eventid()][event.eventemitter()] = self.agent[event.eventemitter()].eventhandler 

    """ Process unsubsribe events """
    def unsubscribe(self, event):         
        logging.debug("Unsubscribe - event: %s", event.dump())
        try:
            del self.subscription[event.eventagent()][event.eventid()][event.eventemitter()]
        except KeyError:
            logging.error("Agent '%s' is not subscribed to event '%s'", event.eventagent(), event.eventid())

    """ Return a list of subscriibers to an event """
    def subscribers(self, event):         
        #logging.debug("Subscribers - event: %s", event.dump())
        #print "GOT HERE0:", self.subscription
        subs = dict()
        if self.subscription.has_key('ALL'):
            if self.subscription['ALL'].has_key('ALL'):
                #print "GOT HERE1 - ALL-ALL"
                subs.update(self.subscription['ALL']['ALL'])
            if self.subscription['ALL'].has_key(event.eventid()):
                #print "GOT HERE2 - ALL-eventid"
                subs.update(self.subscription['ALL'][event.eventid()])
            # avoid sending events to the event emitter
            if subs.has_key(event.eventemitter()): 
                #print "\tRemoving emitter:", event.eventemitter() 
                del subs[event.eventemitter()]
        if self.subscription.has_key(event.eventemitter()):
            if self.subscription[event.eventemitter()].has_key('ALL'):
                #print "GOT HERE3 - eventemitter-ALL"
                subs.update(self.subscription[event.eventemitter()]['ALL'])
            if self.subscription[event.eventemitter()].has_key(event.eventid()):
                #print "GOT HERE4 - eventemitter-eventid"
                subs.update(self.subscription[event.eventemitter()][event.eventid()])
        
        logging.debug("Subscribers found: %i", len(subs))
        return subs

    """
        Given any number of dicts, shallow copy and merge into a new dict,
        precedence goes to key value pairs in latter dicts.
    """
    def merge_dicts(firstdict, *dict_args):
        for dictionary in dict_args:
            firstdict.update(dictionary)


# MAIN #
if __name__ == '__main__':
    mcc = mcp()

    # Most code here needs to be moved to core-logic or user-logic files
    # id, event = '', type = 'message', agent = '', user = '', data = dict()
    tm = event('xmpp_message', 'starting up', 'message', 'xmpp_message', 'USER@DOMAIN')
    mcc.queueevent(tm)

    mcc.scheduler.add('Nightly zwave healNetwork', {'hourlist': [3], 'recurring': True},
                      event('openzwave', 'healNetwork', 'message'))

    mcc.scheduler.add('Porchlight Spring ON Schedule', {'monthnames': ['march', 'april', 'may'], 'hourlist': [20], 'minutelist': [30], 'recurring': True},
                      event('openzwave', 'setValue', 'message', '', '', { 'node': 'RGB Light - Porch', 'name': 'Level', 'value': 50 }))
    mcc.scheduler.add('Porchlight Spring OFF Schedule', {'monthnames': ['march', 'april', 'may'], 'hourlist': [6], 'recurring': True},
                      event('openzwave', 'setValue', 'message', '', '', { 'node': 'RGB Light - Porch', 'name': 'Level', 'value': 0 }))
    mcc.scheduler.add('Porchlight Summer ON Schedule', {'monthnames': ['june', 'july', 'august'], 'hourlist': [21], 'recurring': True},
                      event('openzwave', 'setValue', 'message', '', '', { 'node': 'RGB Light - Porch', 'name': 'Level', 'value': 50 }))
    mcc.scheduler.add('Porchlight Summer OFF Schedule', {'monthnames': ['june', 'july', 'august'], 'hourlist': [5], 'recurring': True},
                      event('openzwave', 'setValue', 'message', '', '', { 'node': 'RGB Light - Porch', 'name': 'Level', 'value': 0 }))
    mcc.scheduler.add('Porchlight Fall ON Schedule', {'monthnames': ['september', 'october', 'november'], 'hourlist': [20], 'recurring': True},
                      event('openzwave', 'setValue', 'message', '', '', { 'node': 'RGB Light - Porch', 'name': 'Level', 'value': 50 }))
    mcc.scheduler.add('Porchlight Fall OFF Schedule', {'monthnames': ['september', 'october', 'november'], 'hourlist': [6], 'recurring': True},
                      event('openzwave', 'setValue', 'message', '', '', { 'node': 'RGB Light - Porch', 'name': 'Level', 'value': 0 }))
    mcc.scheduler.add('Porchlight Winter ON Schedule', {'monthnames': ['december', 'january', 'february'], 'hourlist': [19], 'recurring': True},
                      event('openzwave', 'setValue', 'message', '', '', { 'node': 'RGB Light - Porch', 'name': 'Level', 'value': 50 }))
    mcc.scheduler.add('Porchlight Winter OFF Schedule', {'monthnames': ['december', 'january', 'february'], 'hourlist': [7], 'recurring': True},
                      event('openzwave', 'setValue', 'message', '', '', { 'node': 'RGB Light - Porch', 'name': 'Level', 'value': 0 }))

    mcc.scheduler.add('Thermostat Night Schedule', {'hourlist': [22], 'recurring': True},
                      event('openzwave', 'setValue', 'message', '', '', { 'node': 'Thermostat', 'name': 'Heating 1', 'value': 71.0 }))
    mcc.scheduler.add('Thermostat Day Schedule', {'hourlist': [8], 'recurring': True},
                      event('openzwave', 'setValue', 'message', '', '', { 'node': 'Thermostat', 'name': 'Heating 1', 'value': 74.0 }))
   

    ce = event(**{'id': 'command-manualtest', 'event': 'help', 'type': 'command', 'user': 'USER@DOMAIN', 'data': { 'returnid': 'xmpp_message' }})
    mcc.queueevent(ce)


    # run until kill signal
    signal.pause() 
