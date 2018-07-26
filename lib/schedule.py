#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This core library provides mechanisms to schedule events in the future with several different time specifications.
See timetools for more information on ways to specify time.
"""
from time import time, strftime, localtime
import logging
from threading import Timer

from lib.event import event
from lib.timetools import inseconds
from lib.command import command

logger = logging.getLogger(__name__)

class schedule:
    def __init__(self, queueevent, config):
        self.queueevent = queueevent 
        self.config = config
        self.events = dict()

        #for e in config['events']:
        #    logger.debug('Loading stored event: {}'.format(event))
        #    self.add(e.id, e.when, event(**e.event))

    def add(self, id, when, event):
        interval = inseconds(when)
        target = strftime("%a, %d %b %Y %H:%M:%S %Z", localtime(interval + time()))
        logger.debug("Adding schedule id '{}' to run on {} ({} seconds)".format(id, strftime("%a, %d %b %Y %H:%M:%S %Z", localtime(interval + time())), interval))
        if when.has_key('recurring') and when['recurring']:
            self.events[id] = {'timer': Timer(interval, self.runreschedule, (id, when, event)), 'target': target, 'when': when, 'event': event}
        else:
            self.events[id] = {'timer': Timer(interval, self.run, (id, event)), 'target': target, 'when': when, 'event': event}
        self.events[id]['timer'].start()

    def remove(self, id):
        logger.debug('Removing shedule id: {}'.format(id))
        e = self.events.pop(id, None)
        if e == None:
            logger.debug("Could not remove shedule: '{}' - not found".format(id))
            return True 
            
        e['timer'].cancel()
        return False

    def removeall(self):
        logger.debug('Removing all scheduled events')
        for id in self.events.keys():
            self.remove(id)

    def __str__(self):
        s = str()
        for id in self.events:
            s += "id: {}, target: {}'\n".format(id, self.events[id]['target'])
        return s

    def list(self):
        slist = list()
        for id in self.events:
            slist.append({ 'id': id, 'target': self.events['target'] })
        return slist

    def run(self, id, event):
        logger.debug("Running schedule: '{}' event: '{}'".format(id, event))
        self.queueevent(event)
        self.remove(id)

    def runreschedule(self, id, when, event):
        logger.debug("Running recurring schedule: '{}' event: '{}'".format(id, event))
        self.queueevent(event)
        self.remove(id)
        self.add(id, when, event)

# MAIN #
if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s: %(message)s',
	                datefmt='%Y/%m/%d-%H:%M:%S', level=logging.DEBUG)

    def dummycallback(event):
            logger.debug('Callback received event: %s', event.eventbody())

    s = schedule(dummycallback, {})
    logger.debug('Scheduling events')

    # An example of scheduling Zwave events
    s.add('Nightly zwave healNetwork', {'hourlist': [3], 'recurring': True},
	                      event('openzwave', 'healNetwork', 'message'))

    s.add('Porchlight One-Time 20:28 OFF Schedule', {'hourlist': [20], 'minutelist': [28]},
	                      event('openzwave', 'setValue', 'message', '', '', { 'node': 'RGB Light - Porch', 'name': 'Level', 'value': 0 }))

    s.add('Porchlight Spring ON Schedule', {'monthnames': ['march', 'april', 'may'], 'hourlist': [20], 'minutelist': [30], 'recurring': True},
	                      event('openzwave', 'setValue', 'message', '', '', { 'node': 'RGB Light - Porch', 'name': 'Level', 'value': 50 }))
    s.add('Porchlight Spring OFF Schedule', {'monthnames': ['march', 'april', 'may'], 'hourlist': [6], 'recurring': True},
	                      event('openzwave', 'setValue', 'message', '', '', { 'node': 'RGB Light - Porch', 'name': 'Level', 'value': 0 }))
    s.add('Porchlight Summer ON Schedule', {'monthnames': ['june', 'july', 'august'], 'hourlist': [21], 'recurring': True},
	                      event('openzwave', 'setValue', 'message', '', '', { 'node': 'RGB Light - Porch', 'name': 'Level', 'value': 50 }))
    s.add('Porchlight Summer OFF Schedule', {'monthnames': ['march', 'april', 'may'], 'hourlist': [5], 'recurring': True},
	                      event('openzwave', 'setValue', 'message', '', '', { 'node': 'RGB Light - Porch', 'name': 'Level', 'value': 0 }))

    s.add('Livingroom Dimmer OFF Schedule', {'hourlist': [22], 'recurring': True},
	                      event('openzwave', 'setValue', 'message', '', '', { 'node': 'Dimmer - Livingroom', 'name': 'Level', 'value': 0 }))
    s.add('Livingroom Dimmer ON Schedule', {'hourlist': [22], 'minutes': 1, 'recurring': True},
	                      event('openzwave', 'setValue', 'message', '', '', { 'node': 'Dimmer - Livingroom', 'name': 'Level', 'value': 99 }))    

    logger.debug("Done scheduling events, wait for events to run:\n{}".format(s))


