#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
This core library contains functions for converting and making calculations with time specifications in various formats.
'''

from time import time, strftime, strptime, localtime, mktime
from datetime import timedelta as dt_timedelta
from calendar import monthrange, monthcalendar, day_name, month_name
from random import randint

from logging import getLogger, basicConfig
from logging import DEBUG as logging_DEBUG 

logger = getLogger(__name__)
config = dict() 

'''
    Covert the time delta definitions to seconds from now
'''
def timedelta(when):
    # FIXME: make DST aware
    whentd = dict()
    for x in ('seconds', 'minutes', 'hours', 'days', 'months', 'years'):
        if x in when and when[x] != None: whentd[x] = when[x]
    if any(whentd): 
        logger.debug('WHENTD: {}'.format(whentd))
        return dt_timedelta(**whentd).total_seconds()

    return None 

'''
    Covert specific time definitions to a struct_time object or equivalent list 
'''
def specifictime(when, nowst = localtime()):
    # FIXME: make DST aware
    # TODO: load formats from config

    st = None
    if 'datetime' in when and when['datetime'] != None:
        logger.debug("DATETIME:", when['datetime'])
        st = strptime(when['datetime'], config.get('datetimeformat', '%Y-%m-%d %H:%M'))
        return st

    if 'date' in when and when['date'] != None:
        logger.debug("DATE:", when['date'])
        st = strptime(when['date'], config.get('dateformat', '%Y-%m-%d'))

    if 'time' in when and when['time'] != None:
        logger.debug("TIME:", when['time'])
        stt = strptime(when['time'], config.get('timeformat', '%H:%M'))
        if 'date' in when and when['date'] != None:
            st = [ st[0], st[1], st[2], stt[3], stt[4], stt[5], st[6], st[7], st[8] ]
        else:
            st = [ nowst[0], nowst[1], nowst[2], stt[3], stt[4], stt[5], nowst[6], nowst[7], nowst[8] ]
        # FIXME handle negative seconds due to current time being past specified time (add a day)

    return st


'''
    Use the wildcard time definition to match next occurrence in the future and return a struct_time object 
'''
    # struct_time(tm_year=2018, tm_mon=5, tm_mday=22, tm_hour=12, tm_min=50, tm_sec=40, tm_wday=1, tm_yday=142, tm_isdst=1)
    # FIXME: make DST aware
def matchtime(when, nowst, level = 0, whenst = None, usemin = False, lastmatch = None):
    if level == 0: nowst = localtime()

    keys = ('yearlist', 'monthlist', 'daylist', 'hourlist', 'minutelist', 'secondlist')
    minmax = { 'monthlist': { 'min': 1, 'max': 12 }, 
               'daylist':   { 'min': 1, 'max': 31 },
               'hourlist':  { 'min': 0, 'max': 23 },
               'minutelist':{ 'min': 0, 'max': 59 },
               'secondlist':{ 'min': 0, 'max': 59 } }

    key = keys[level]
    whenlist = list()

    if lastmatch == None:
        for k in keys:
            if when.has_key(k) and when[k] != None:
                lastmatch = keys.index(k)

    if whenst == None: 
        whenst = list(nowst)
        whenst[8] = -1

    logger.debug('{}WHENST: {} NOWST: {} LEVEL: {}'.format('  ' * level, whenst, list(nowst), level))

    if not when.has_key(key) or when[key] == None:
        logger.debug('USEMIN: {}'.format(usemin))
        if level == 0:
            whenlist = [nowst.tm_year, nowst.tm_year + 1]
        elif level == 2 and when.has_key('dowlist') and not when['dowlist'] == None:
            m = monthcalendar(whenst[0], whenst[1])
            for w in m:
                for dow in when['dowlist']:
                    if w[dow] > 0: 
                        whenlist.append(w[dow])
                        logger.debug('{}WHENLIST1: {}'.format('  ' * level, whenlist))
        elif level == 2:
            days = [ minmax[key]['min'], monthrange(whenst[0], whenst[1])[1] ]
            logger.debug('{}MONTHRANGE: {}'.format('  ' * level, monthrange(whenst[0], whenst[1])))
            logger.debug('{}DAYS1: {}'.format('  ' * level, days))
            if not usemin:
                days[0] = nowst[2]
             
            logger.debug('{}DAYS2: {}'.format('  ' * level, days))
            whenlist = range(*days) or [days[1]]

            logger.debug('{}WHENLIST2: {}'.format('  ' * level, whenlist))
        else:
            if not usemin:
                whenlist = range(nowst[level], minmax[key]['max'] + 1)
                logger.debug('{}WHENLIST3: {}'.format('  ' * level, whenlist))
            else:
                whenlist = range(minmax[key]['min'], minmax[key]['max'] + 1)
                logger.debug('{}WHENLIST4: {}'.format('  ' * level, whenlist))
    else:
        whenlist = when[key]
        logger.debug('{}WHENLIST5: {}'.format('  ' * level, whenlist))

    whensttmp = list(whenst)
    whensttmp[level] = whenlist[-1]
    if mktime(whensttmp) < mktime(nowst): # shortcut
        return None

    for x in whenlist:
        if level <= 5: logger.debug('{}{} - level {}: {}'.format('  ' * level, key, level, x))
        whenst[level] = x
        secres = mktime(whenst) - mktime(nowst)
        logger.debug('SECRES: {} - lastmatch: {}'.format(secres, lastmatch))
        if secres == 0 and when.has_key('recurring') and when['recurring'] and lastmatch == level:
            logger.debug('Schedule is recurring, continuing'.format(lastmatch))
            continue
        elif secres >= 0:
            if secres > 0: usemin = True
            logger.debug('{} is >= nowst: {} seconds: {}'.format('  ' * level, nowst[level], secres))
            if level == 5:
                logger.debug('MATCHED TIME: {}'.format(strftime("%a, %d %b %Y %H:%M:%S %Z", whenst)))
                logger.debug('WHENST: {}'.format(whenst))
                return whenst 
        else: 
            logger.debug('{}->Going to next, seconds: {}'.format('  ' * level, secres))

        if level < 5: 
            wst = matchtime(when, nowst, level + 1, whenst, usemin, lastmatch)
            if wst != None: return wst 

    return None 


'''
    Convert a list of day names to a list of day of week numbers 
'''
def convertdaynames(daynames):
    tempnames = [d.lower() for d in daynames]
    dowlist = list()
    
    for i,cd in enumerate(day_name):
        if cd.lower() in tempnames:
            dowlist.append(i)
            tempnames.remove(cd.lower())

    if tempnames:
        logger.warning("WARNING - could not match day name:", tempnames)

    return dowlist


'''
    Convert a list of month names to a list of month numbers 
'''
def convertmonthnames(monthnames):
    tempnames = [m.lower() for m in monthnames]
    monthlist = list()
    
    for i,cm in enumerate(month_name):
        if i == 0: continue
        if cm.lower() in tempnames:
            monthlist.append(i)
            tempnames.remove(cm.lower())

    if tempnames:
        logger.warning("WARNING - could not match month name:", tempnames)

    return monthlist


'''
    Randomly adjust the time forward or back by the specified number of units
    For example: if you pass randsecs: 30, the time will be randomly adjusted
    from -30 to 30 seconds (1 minute total range).
'''
def randomize(when, seconds = None):
    randsecs = 0
    if 'randseconds' in when and when['randseconds'] != None:
        randsecs += when['randseconds']
    if 'randminutes' in when and when['randminutes'] != None:
        randsecs += timedelta({'minutes': when['randminutes']})
    if 'randhours' in when and when['randhours'] != None:
        randsecs += timedelta({'hours': when['randseconds']})
    if 'randdays' in when and when['randdays'] != None:
        randsecs += timedelta({'days': when['randdays']})

    if seconds != None and randsecs:
        logger.debug("Adjusting time randomly + or - seconds:", randsecs)
        seconds += randint(-randsecs, randsecs)
        if seconds < 0: seconds = 0

    return seconds


'''
    Convert the various time definitions to a time in seconds from now
'''
# TODO: convert subroutines to return time/date structure that inseconds will convert to seconds from now
# TODO: modify subroutines to accept nowst peramiter for current time like matchtime
def inseconds(when, nowst = None, seconds = None):
    # FIXME: make DST aware
    if not nowst: nowst = localtime()
    sectmp = timedelta(when)
    if sectmp and seconds: seconds += sectmp
    elif sectmp: seconds = sectmp

    st = specifictime(when, nowst)

    if st:
        if seconds == None: seconds = 0
        seconds += mktime(st) - mktime(nowst) 
    elif ('secondlist' in when and when['secondlist'] != None) or \
         ('minutelist' in when and when['minutelist'] != None) or \
         ('hourlist' in when and when['hourlist'] != None) or \
         ('daylist' in when and when['daylist'] != None) or \
         ('dowlst' in when and when['dowlist'] != None) or \
         ('monthlist' in when and when['monthlist'] != None) or \
         ('daynames' in when and when['daynames'] != None) or \
         ('monthnames' in when and when['monthnames'] != None) :

        if 'daynames' in when and when['daynames'] != None:
            when['dowlist'] = convertdaynames(when['daynames'])
        if 'monthnames' in when and when['monthnames'] != None:
            when['monthlist'] = convertmonthnames(when['monthnames'])

        mst = matchtime(when, nowst)

        if mst:
            if seconds == None: seconds = 0
            seconds += mktime(mst) - mktime(nowst)

    if seconds != None: 
        seconds = randomize(when, seconds)

    return seconds


# calculate how long it was ago
def howlongago(seconds):
    sec = time.time() - float(seconds)
    if sec < 60:
        value = sec
        unit = 'second'
    elif sec < 3600:
        value = int(sec / 60)
        unit = 'minute'
    elif sec < 86400:
        value = int(sec / 60 / 60)
        unit = 'hour'
    elif sec < 604800:
        value = int(sec / 60 / 60 / 24)
        unit = 'day'
    elif sec < 2592000:
        value = int(sec / 60 / 60 / 24 / 7)
        unit = 'week'
    else:
        value = int(sec / 60 / 60 / 24 / 30)
        unit = 'month'

    if value > 1: unit += 's'
    return '{} {}'.format(value, unit)


### Main ###

if __name__ == "__main__":
    import sys 
    import argparse

    basicConfig(format='%(asctime)s %(levelname)s %(name)s: %(message)s',
                            datefmt='%Y/%m/%d-%H:%M:%S', level=logging_DEBUG)

    parser = argparse.ArgumentParser(description="Time parsing, matching and conversion tools")
    # timedelta
    parser.add_argument("--seconds", type=int, help="Seconds from now")
    parser.add_argument("--minutes", type=int, help="Minutes from now")
    parser.add_argument("--hours", type=int, help="Hours from now")
    parser.add_argument("--days", type=int, help="Days from now")
    parser.add_argument("--months", type=int, help="Months from now")
    # specifictime
    parser.add_argument("--time", type=str, help="A specific time in the format 'YYYY-MM-DD'")
    parser.add_argument("--date", type=str, help="A specific date in ISO 8601 format 'YYYY-MM-DD'")
    parser.add_argument("--datetime", type=str, help="A specific date and time in this format 'YYYY-MM-DD HH:MM'")
    # matchtime
    parser.add_argument("--secondlist", type=int, nargs='+', help="One or more seconds to match")
    parser.add_argument("--minutelist", type=int, nargs='+', help="One or more minutes to match")
    parser.add_argument("--hourlist", type=int, nargs='+', help="One or more hours to match")
    parser.add_argument("--daylist", type=int, nargs='+', help="One or more days to match, use day number in month")
    parser.add_argument("--dowlist", type=int, nargs='+', help="One or more days of the week to match, use day number in week")
    parser.add_argument("--daynames", type=str, nargs='+', help="Name of one or more days to match")
    parser.add_argument("--monthlist", type=int, nargs='+', help="One or more months to match, use day number in year")
    parser.add_argument("--monthnames", type=str, nargs='+', help="Name of one or more months to match")
    # randomize
    parser.add_argument("--randseconds", type=int, help="Number of seconds to randomly adjust the resulting time")
    parser.add_argument("--randminutes", type=int, help="Number of minutes to randomly adjust the resulting time")
    parser.add_argument("--randhours", type=int, help="Number of hours to randomly adjust the resulting time")
    parser.add_argument("--randdays", type=int, help="Number of days to randomly adjust the resulting time")

    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    print 'Start:', time()
    print "Input:", vars(args) 
    seconds = inseconds(vars(args))
    print "Seconds from now:", seconds
    print "Seconds to date (strftime):", strftime("%a, %d %b %Y %H:%M:%S %Z", localtime(seconds + time()))
