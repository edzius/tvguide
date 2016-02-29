#!/usr/bin/env python2

import argparse

import tvfetch

def main():
    parser = argparse.ArgumentParser(description='TV Guide debug parser')
    parser.add_argument('source', metavar='FILE', action='store', type=str, help='File to parse')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-c', '--channel', action='store_true', help='Parse channels list')
    group.add_argument('-p', '--programme', action='store_true', help='Parse programme data')
    args = parser.parse_args()

    try:
        fp = open(args.source, 'r')
        data = fp.read()
        fp.close()
    except IOError:
        parser.error("No such file '%s'" % args.source)

    if args.channel:
        parsed = tvfetch.parseChannels(data, False)
        for channel in parsed:
            print(channel)
    elif args.programme:
        parsed = tvfetch.parseSchedule(data, False)
        for data in parsed:
            print(data['date'])
            for show in data['shows']:
                print(show)

main()
