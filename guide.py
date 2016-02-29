#!/usr/bin/env python2

# Vendor modules
import re
import sys
import inspect
import argparse
import datetime
# Local modules
import config
import tvfetch
import tvselect


EXEC_PATH = inspect.getframeinfo(inspect.currentframe()).filename

def now(days=0):
    delta = datetime.timedelta(days=days)
    return datetime.datetime.now() + delta

def out(fmt, *args):
    msg = str(fmt) % args
    msg = '%s\n' % msg
    sys.stdout.write(msg.encode('utf-8'))

def err(fmt, *args):
    msg = str(fmt) % args
    msg = '%s\n' % msg
    sys.stdout.write(msg.encode('utf-8'))

def printAll(items):
    for item in items:
        out(item)
    err(len(items))

def printDict(dataDict):
    for key, value in dataDict.items():
        out('%30s | %s', key, value)

class DateType(object):

    RELATIVE_MATCHER = re.compile("([wd])(\-?\d+)")

    def __init__(self):
        pass

    def __call__(self, string):
        relDate = self.RELATIVE_MATCHER.findall(string)
        if relDate:
            current = datetime.datetime.now()
            for mode, offset in relDate:
                if mode == 'd':
                    current += datetime.timedelta(days=int(offset))
                elif mode == 'w':
                    current += datetime.timedelta(weeks=int(offset))

            return current.date()
        else:
            return datetime.datetime.strptime(string, '%Y.%m.%d').date()

    def __repr__(self):
        return 'date'

class TimeType(object):

    RELATIVE_MATCHER = re.compile("([hm])(\-?\d+)")

    def __init__(self):
        pass

    def __call__(self, string):
        relTime = self.RELATIVE_MATCHER.findall(string)
        if relTime:
            current = datetime.datetime.now()
            for mode, offset in relTime:
                if mode == 'h':
                    current += datetime.timedelta(hours=int(offset))
                elif mode == 'm':
                    current += datetime.timedelta(minutes=int(offset))

            return current.time()
        else:
            return datetime.datetime.strptime(string, '%H:%M').time()

    def __repr__(self):
        return 'time'

def main():
    parser = argparse.ArgumentParser(description='TV Guide harvest tool')
    group_action = parser.add_mutually_exclusive_group()
    group_action.add_argument('-c', '--channels', action='store_true', help='List available TV guide channels')
    group_action.add_argument('-g', '--groups', action='store_true', help='List available TV guide channel categories')
    group_channels = group_action.add_argument_group(title='Schedule', description='Show channels schedule')
    group_channels.add_argument('name', metavar='CHANNEL|CATEGORY', action='store', type=str, help='Channel/Category name', nargs='*')
    group_channels.add_argument('-s', '--show', action='store', type=str, help='Show to select')
    group_date = group_channels.add_mutually_exclusive_group()
    group_date.add_argument('-d', '--date', action='store', type=DateType(), help='Date to select')
    group_date_range = group_date.add_argument_group()
    group_date_range.add_argument('--date-from', action='store', type=DateType(), help='Start date to select')
    group_date_range.add_argument('--date-to', action='store', type=DateType(), help='End date to select')
    group_time = group_channels.add_mutually_exclusive_group()
    group_time.add_argument('-t', '--time', action='store', type=TimeType(), help='Time to select')
    group_time_range = group_date.add_argument_group()
    group_time_range.add_argument('--time-from', action='store', type=TimeType(), help='Start time to select')
    group_time_range.add_argument('--time-to', action='store', type=TimeType(), help='End time to select')
    args = parser.parse_args()

    options = config.load(EXEC_PATH)
    store = tvfetch.ChannelStore(options)
    guide = tvselect.ShowSelect(store)

    channelMap = tvselect.getChannelsMap(store)
    categoryMap = tvselect.getCategoriesMap(store)

    if args.channels:
        printDict(channelMap)
        return
    if args.groups:
        printDict(categoryMap)
        return

    targetName = []
    targetGroup = []
    for name in args.name:
        if name in channelMap:
            targetName.append(name)
        elif name in categoryMap:
            if len(targetGroup) > 0:
                err('Allowed to set only one channel group. Ignoring: %s', name)
            else:
                targetGroup.append(name)
        else:
            err('Unknown channel/category name: %s', name)

    if len(targetName) == 0:
        targetName = None
        if len(targetGroup) == 0 and args.name:
            return
    if len(targetGroup) == 0:
        targetGroup = None

    if args.date == None and args.date_from == None and args.date_to == None:
        args.date = datetime.datetime.now().date()
    if not targetName:
        if args.time == None and args.time_from == None and args.time_to == None:
            args.time = datetime.datetime.now().time()

    selected = guide.select(targetName, targetGroup, args.show, args.date, args.date_from, args.date_to, args.time, args.time_from, args.time_to)
    preciseChannel = targetName and len(targetName) == 1
    preciseTime = args.date and args.time
    for show in selected:
        if preciseChannel:
            texts = []
            if show['title']:
                texts.append(show['title'])
            if show['description']:
                texts.append(show['description'])
            live = show['live'] and '*' or ' '
            out('%s%s - %s | %s', live, show['time'], show['ends'], ' -- '.join(texts))
        elif preciseTime:
            out('%s - %s | %-25s | %s', show['time'], show['ends'], channelMap[show['channel']], show['title'])
        else:
            live = show['live'] and '*' or ' '
            out('%s%s - %s | %-25s | %s', live, show['time'], show['ends'], channelMap[show['channel']], show['title'])

main()
