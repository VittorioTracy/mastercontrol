#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
This core library provides command registration, parsing and processing.
Other components register commands either with the add method or through a command register event.
'''

import re
from logging import getLogger

from lib.event import event

# Global Variables
logger = getLogger(__name__)

COMMANDS = { 'help':   { 'description': 'List available commands',
                         'authorized': 'ALL',
                         'handlername': 'help' },
           }

class command:
    def __init__(self, eventcallback, state = dict()):
        self.eventcallback = eventcallback
        self.commands = state
        # register default commands
        self.add(COMMANDS)
        # register commands from state
        #self.add(state)

    # add a command
    def add(self, command):
        if not command: 
            logger.error("Command not defined")
            return

        for cmd in command:
            if cmd in self.commands:
                logger.critical("Command '{}' is already defined, skipping".format(cmd))
                continue
                
            if not (type(command[cmd]) is dict):
                logger.critical("Command '{}' values not passed dict, skipping {}".format(cmd, command[cmd]))
                continue

            subcmd = next(iter(command[cmd])) 
            if not (('description' in command[cmd] and 
                     'authorized' in command[cmd] and 
                     ('handler' in command[cmd] or 'handlername' in command[cmd] or 'handlerevent' in command[cmd])) or
                    (type(command[cmd][subcmd]) is dict and
                     'description' in command[cmd][subcmd] and
                     'authorized' in command[cmd][subcmd] and
                     ('handler' in command[cmd][subcmd] or 'handlername' in command[cmd][subcmd] or 'handlerevent' in command[cmd][subcmd]))):
                logger.critical("Command '{}' details not passed, skipping {}".format(cmd, command[cmd]))
                continue
                
            logger.debug("Adding command: {}".format(cmd))
            self.commands[cmd] = command[cmd]

    # remove a command
    def remove(self, command):
        if not command: 
            logger.error("Command to remove not defined")
        elif command not in self.commands:
            logger.error("Command not registered")
        else:
            logger.debug("Removing command: {}".format(command))
            del self.commands[command]

    # list command information
    def list(self):
        lst = list()
            
        for comm in sorted(self.commands.iterkeys()):
            if 'description' in self.commands[comm]:
                lst.append(comm) 
            else:
                for subc in self.commands[comm]:
                    lst.append('{} {}'.format(comm, subc))
        return lst

    def parse(self, msg):
        # parse command message
        words = msg.split()
        logger.debug("got words: {}".format(words))
        if len(words) >= 1:
            words[0] = words[0].lower()
        if len(words) >= 2: 
            words[1] = words[1].lower()
        if not words:
            words.append('help')

        # find command
        args = list() 
        cmdinfo = dict() 

        first = 2
        if words[0] in self.commands:
            logger.debug("Found first word in commands")
            if 'description' in self.commands[words[0]]:
                logger.debug("Found single word command: '{}'".format(words[0]))
                cmdinfo = self.commands[words[0]]
                first = 1
            elif len(words) > 1 and words[1] in self.commands[words[0]]:
                logger.debug("Found command: '{} {}'".format(words[0], words[1]))
                cmdinfo = self.commands[words[0]][words[1]]
            else:
                logger.debug("Command not found: '{}'".format(words[0]))
                return "Command not found: '{}'".format(words[0]), None
        else:
            logger.debug("Command not found: '{}'".format(words[0]))
            return "Command not found: '{}'".format(words[0]), None

        logger.debug("Command info: {}".format(cmdinfo))
        args = words[first:]
        return cmdinfo, args

    def authorize(self, user, info):
        # check permissions
        if user not in info['authorized'] and info['authorized'] != 'ALL':
            logger.error("Not authorized")
            return "Error: Not authorized"

    def validate(self, info):
        # validate command input
        try: isopt = commandInfo['optional']
        except KeyError:
            isopt = False
        try: regex = commandInfo['validate']
        except KeyError:
            regex = None

        if regex:
            logger.debug("Found regex for validation: {}".format(regex))
            if len(words) < 3 and not isopt:
                logger.error("Command is missing 3rd paramiter")
                return "Error: Command is missing 3rd paramiter" 
            # check input against regex 
            if len(words) > 2 and not re.match(regex, words[2]):
                logger.error("Bad input for 3rd paramiter")
                return "Error: Bad input for 3rd paramiter"


    # run command
    def run(self, cmdinfo, args, user):
        logger.debug("Got command args: {}".format(args))
        #logger.debug("globals: {}".format(globals()))
        #logger.debug("locals: {}".format(locals()))
        #reply = globals()['self.'+ commandInfo['handler']](args)
        reply = str() 
        # execute a callable object
        if 'handler' in cmdinfo:
            logger.debug("Found command handler: {}".format(cmdinfo['handler']))
            logger.debug("Command function type: {}".format(type(cmdinfo['handler'])))
            logger.debug("Command function callable? {}".format(callable(cmdinfo['handler'])))
            if callable(cmdinfo['handler']):
                reply = cmdinfo['handler'](args)
            else:
                logger.critical("Command defined is not callable, skipping: {}".format(cmdinfo['handler']))
                reply = 'An error occurred'
        # create an event
        elif 'handlerevent' in cmdinfo:
            handevent = dict(cmdinfo['handlerevent'])
            logger.debug("Found command handler event: {}".format(handevent))
            if not 'data' in handevent: handevent['data'] = dict()
            handevent['data']['args'] = args
            handevent['user'] = user 
            he = event(**handevent)
            self.eventcallback(he)
        # run a function by name
        else:
            logger.debug("Found command handler name: {}".format(cmdinfo['handlername']))
            func = getattr(self, cmdinfo['handlername'], None) 
            logger.debug("Command function type: {}".format(type(func)))
            if func is None: return "Could not locate function"

            logger.debug("Got function: {}".format(func))
            reply = func(args)

        #reply = eval(('self.'+ commandInfo['handler'])(args))
        #reply = globals()[commandInfo['handler']](args)
        logger.debug("Got reply:\n{}".format(reply))
        if reply is None:
           return('no response')
        else:
           return(reply)


    def help(self, args):
        logger.debug("Command: 'help'")
        msg = str()

        for comm in sorted(self.commands.iterkeys()):
            logger.debug("Command:\n{}\n".format(self.commands[comm]))
            if 'description' in self.commands[comm]:
                msg += "{:10}{:15}{}\n".format(comm, ' ', self.commands[comm]['description'])
            else:
                msg += comm +"\n"
                for subc in sorted(self.commands[comm].iterkeys()):
                    msg += "{:10}{:15}{}\n".format('', subc, self.commands[comm][subc]['description'])
        return msg 

    def handle(self, user, msg):
        logger.debug("handle got command: {}".format(msg))
        cmdinfo, args = self.parse(msg)
        if not type(cmdinfo) is dict:
            return cmdinfo 
        # FIXME
        #ret = self.authorize(user, cmdinfo)
        #ret = self.validate(cmdinfo)
        ret = self.run(cmdinfo, args, user)
        return ret

    # event handler
    # events of type 'command' are routed to this function by the mcp dispatcher
    def event(self, cmdevent):
        data = cmdevent.eventdata()
        body = cmdevent.eventbody()
        if 'operation' in data:
            if data['operation'] == 'add':
                self.add(data['command'])
            elif data['operation'] == 'remove':
                self.add(data['command'])
            elif data['operation'] == 'list':
                clist = self.list()
                if 'returnevent' in data:
                    data['returnevent'].data['return'] = clist
                    self.eventhcallback(data['returnevent'])
        elif len(body) > 0:
            ret = self.handle(cmdevent.eventuser(), body)
            # send response
            if 'returnid' in data:
                re = event(**{'id': data['returnid'], 'event': ret, 'user': cmdevent.eventuser() })
                self.eventcallback(re)
        else:
            logger.critical("Cannot process event: {}".format(cmdevent.dump()))
        #cmdinfo, args = self.parse(msg)
        #if not type(cmdinfo) is dict:

        
### MAIN ###
if __name__ == "__main__":
    from sys import argv
    from logging import basicConfig
    from logging import DEBUG as logging_DEBUG
    basicConfig(format='%(asctime)s %(levelname)s %(name)s: %(message)s',
                datefmt='%Y/%m/%d-%H:%M:%S', level=logging_DEBUG)
    argv.pop(0) # remove program name from arg list

    def dummycallback(event):
        logger.debug("Dummycallback got event: {}".format(event.dump()))

    c = command(dummycallback);

    # direct
    logger.debug('Command list: {}'.format(c.list()))
    response = c.handle('someuser@fake.com', ' '.join(argv))
    logger.debug('Got command response: {}'.format(response))
    # using event
    e1 = event(**{'id': 'eventid1', 'event': 'help', 'type': 'command', 'user': 'bob@home', 'data': { 'returnid': 'someid' }})
    c.event(e1)
