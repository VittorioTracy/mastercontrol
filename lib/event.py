#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This core library defines the event object. 
Events are the main means of communication between agents and the mcp core. 
NOTE: The structure of this object has not been finalized.

Event types:
An event can represent a subscribe/unsubscribe request, a message, usermessage or command.
A subscribe request can be used to match other events or event emitters using using specific agent or event ids or regular expressions.
A message event is for passing a message string between agents/components.
A usermessage event is to represent a message send on behalf of a user.
"""

#from re import sub
from re import compile, match, sub
from inspect import getmodule, currentframe, stack

agentregex = compile('^agent\..+$')

class event:
    def __init__(self, id, event = '', type = 'message', agent = '', user = '', data = dict()):
        self.id = id
        self.body = event
        self.type = type
        self.agent = agent
        self.user = user
        self.data = data
        self.emitter = getmodule(currentframe().f_back).__name__
        agentmatch = agentregex.match(self.emitter) 
        self.agentevent = True
        # this event was created by the mcp core 
        if not agentmatch:
            self.emitter = currentframe().f_back.f_code.co_name
            self.agentevent = False 

    def __eq__(self, other):
        print "EQ got self:\n\t", self, "\nother:\n\t", other
        return True

    def __str__(self):
        return str(self.body)

    def dict(self):
        return { 'agent': self.agent, 'id': self.id, 'type': self.type,
                 'event': self.body, 'user': self.user, 'emitter': self.emitter, 'agentevent': self.agentevent }

    """ Return the event id.
    """
    def eventid(self):
        return self.id
    
    """ Return the event.
    """
    def eventbody(self, body = None):
        if body != None:
            self.body = body
        else: 
            return self.body

    """ Return the event type.
        Valid event types: subscribe, unsubscribe, message, usermessage, command
    """
    def eventtype(self):
        return self.type
    
    """ Return the agent id.
    """
    def eventagent(self):
        return self.agent

    """ Return the event user (usermessage type events).
    """
    def eventuser(self):
        return self.user

    """ Return the event data
        Event data can consist of a dictionary with data to be passed to the subscriber
    """
    def eventdata(self):
        return self.data

    """ Return the event emitter.
    """
    def eventemitter(self):
        return self.emitter

    """ Return True or False whether the event is from an agent.
    """
    def isagentevent(self):
        return self.agentevent

    def dump(self):
        return "emitter: '{}' id: '{}' event: '{}' type: '{}' agent: '{}' user: '{}' data: '{}' agentevent: '{}'".format(self.emitter,
            self.id, self.body, self.type, self.agent, self.user, self.data, self.agentevent)

# MAIN #
if __name__ == '__main__':
    ev1 = event('eventid1', 'event1')
    ev2 = event(**{'id': 'eventid2', 'event': 'event2', 'type': 'eventtype2'})

    print 'Created events:', ev1, ev2
    print "\t", ev1.dump(), "\n\t", ev2.dump()

    print "event1 id:", ev1.eventid()
    print 'event1 eventbody:', ev1.eventbody()
    print 'event1 eventtype:', ev1.eventtype()
    print 'event1 agent:', ev1.eventagent()
    print 'event1 user:', ev1.eventuser()
    print 'event1 emitter:', ev1.eventemitter() 


