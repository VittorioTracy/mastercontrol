#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This agent uses the Linux inotify subsystem to watch for filesystem changes and then send MCP events.
"""
import logging
import threading

from inotify_simple import INotify, flags

import lib.event

logger = logging.getLogger(__name__)

class inotify:
    def __init__(self, config, state, eventcallback):
        self.config  = config
        self.state = state
        # register messsage handler
        self.eventcallback = eventcallback
        self.run = True
        
        # id, event = '', type = 'message', agent = '', user = '', data = dict()
        # subscribe to shutdown event
        eventcallback(lib.event.event('shutdown', '', 'subscribe', 'shutdown'))
        # subscribe to inotify_INSTANCEID events
        eventcallback(lib.event.event(config['instanceid'], '', 'subscribe', 'ALL'))
        #self.client.RegisterHandler('message', self.receive)
        self.daemonizeit()

    def shutdown(self):
        logger.debug("Shutdown called")
        self.run = False
        logger.info("Shutdown complete")

    def eventhandler(self, event):
        logger.debug("Eventhandler - event: %s", event.dump())
        if event.eventid() == 'shutdown':
            logger.debug("Got shutdown event")
            self.shutdown()
        elif event.eventtype() == 'message':
            logger.debug("Got message event")
            # FIXME:
            # add ability to watch or stop watching

    def setupandloop(self):
        self.inotify = INotify()
        # FIXME: make flags configuratble
        watch_flags = flags.CREATE | flags.DELETE | flags.CLOSE_WRITE | flags.DELETE_SELF
        #watch_flags = flags.CREATE | flags.DELETE | flags.MODIFY | flags.CLOSE_WRITE | flags.DELETE_SELF
        for i in self.config['watch']:
            logging.debug('Watching: %s', i)
            wd = self.inotify.add_watch(i, watch_flags)

        # loop while run is True
        while self.run:
            # wait for events for 1 second
            for event in self.inotify.read(timeout=1000):
                print(event)
                # FIXME
                # id, event = '', type = 'message', ageent = '', user = ''
                self.eventcallback(lib.event.event(self.config['instanceid'], event, 'message', '', '', {'flags': str(flags.from_mask(event.mask)), 'event': event}))
                #for flag in flags.from_mask(event.mask):

    def daemonizeit(self):
        self.thread = threading.Thread(name=self.config['instanceid'], target=self.setupandloop)
        self.thread.setDaemon(False)
        self.thread.start()

    # FIXME: add method to add watching
    # FIXME: add method to remove watching


### Main ###
if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s: %(message)s',
                            datefmt='%Y/%m/%d-%H:%M:%S', level=logging.DEBUG)

    def dummycallback(event):
        logger.debug('Received message: %s', event.eventbody())

    i = inotify({'instanceid': 'inotifytest', 'watch': ['/tmp/']}, {}, dummycallback)
    from time import sleep
    logger.debug('Running for 300 seconds')
    sleep(300)
    i.shutdown()
