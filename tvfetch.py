
import os
import re
import json
import logging
from datetime import datetime
from bs4 import BeautifulSoup

import web

log = logging.getLogger(__name__)


UNICODE_MAP = {
    260: 'A',
    261: 'a',
    268: 'C',
    269: 'c',
    278: 'E',
    279: 'e',
    280: 'E',
    281: 'e',
    302: 'I',
    303: 'i',
    352: 'S',
    353: 's',
    362: 'U',
    363: 'u',
    370: 'U',
    371: 'u',
    381: 'Z',
    382: 'z'
}

def fallbackEncoding(line):
    def mutate(char):
        code = ord(char)
        if code in UNICODE_MAP:
            char = UNICODE_MAP[code]
        return char
    return "".join(map(mutate, line))

def reduceCharset(line):
    return line.lower().replace(' ', '-')

def readJson(fileName):
    try:
        fp = open(fileName, 'r')
        data = json.load(fp)
        fp.close()
        return data
    except Exception as e:
        log.debug('Failed read JSON: %s', fileName)
        return

def writeJson(fileName, data):
    try:
        fp = open(fileName, 'w')
        json.dump(data, fp)
        fp.close()
        return True
    except Exception as e:
        log.warn('Failed read JSON: %s', fileName)
        return False

def ensureSoup(data):
    if type(data) == str:
        return BeautifulSoup(data, 'html.parser')
    return data

def parseChannels(content, quiet=True):
    def doFixup(channels):
        if not channels or len(channels) == 0:
            return channels

        chLink = re.compile('([\w\-]+)\/\d+$')
        for channelInfo in channels:
            match = chLink.search(channelInfo['link'])
            if match:
                channelInfo['name'] = match.group(1)
            else:
                channelInfo['name'] = reduceCharset(fallbackEncoding(channelInfo['label']))

            channelInfo['group'] = reduceCharset(fallbackEncoding(channelInfo['category']))

        return channels

    def doParse(html):
        chgroup = html.select("#topsearch_form")[0]
        chstore = chgroup.select('script')[0]
        chmatch = re.search("(\[.*\])", chstore.get_text())
        chjson = chmatch.group(1)
        return json.loads(chjson)

    content = ensureSoup(content)
    if quiet:
        try:
            return doFixup(doParse(content))
        except Exception as e:
            log.warn('Failed channels parse: %s', e.message)
            return None
    else:
        return doFixup(doParse(content))

def parseSchedule(content, quiet=True):
    def doParse(html):
        result = []
        today = datetime.now()
        chgroup = html.select(".channel-list")[0]
        chstore = chgroup.select('.channel')
        for chdata in chstore:
            head = chdata.select('header')[0].get_text().strip()
            date = re.search("(\d\d\-\d\d)", head).group(1)
            date = "%s-%s" % (today.year, date,)

            records = []

            schedule = chdata.select('div.item')
            for entry in schedule:
                entryFields = entry.select('span')
                timeitem = entryFields[0]
                time = timeitem.get_text().strip()
                name = timeitem.next_sibling.strip()
                if not name and len(entryFields) > 1:
                    name = entryFields[1].get_text()

                infoitem = entry.select('.description')
                if len(infoitem) > 0:
                    info = infoitem[0].get_text().strip()
                else:
                    info = ''

                records.append({
                    'date': date,
                    'time': time,
                    'title': name,
                    'description': info
                })

            result.append({
                'date': date,
                'shows': records
            })

        return result

    content = ensureSoup(content)
    if quiet:
        try:
            return doParse(content)
        except Exception as e:
            log.warn('Failed schedule parse: %s', e.message)
            return None
    else:
        return doParse(content)

class ChannelStore:

    CHANNELS_URL="http://www.tvprograma.lt/"
    SCHEDULE_URL_SELF="http://www.tvprograma.lt/tv-programa/televizija/%s/%s"
    SCHEDULE_URL_DATE="http://www.tvprograma.lt/tv-programa/televizija/%s/%s/%s"

    def __init__(self, params):
        self.params = params
        self.http = web.Http(self.params)

    def __getChannelsCache(self):
        return os.path.join(self.params.storage_dir, 'channels.json')

    def __getScheduleCache(self, channel, date):
        fileName = "%s-%s.json" % (channel, date.strftime("%Y%m%d"))
        return os.path.join(self.params.storage_dir, fileName)

    def getChannelList(self):
        log.debug('getChannelList()')
        channels = self.readChannelList()
        # Explicitly check None because empty lists is negative result too
        if channels != None:
            log.debug('Using cached channels list')
            return channels

        channels = self.harvestChannelList()
        if not channels:
            log.warn('Failed channel list harvest')
            return None

        self.saveChannelList(channels)
        return channels

    def getChannelSchedule(self, channel, date=None):
        log.debug('getChannelSchedule(): %s (%s)', channel, date)
        schedule = self.readChannelSchedule(channel, date)
        # Explicitly check None because empty lists is negative result too
        if schedule != None:
            log.debug('Using cached channel schedule: %s (%s)', channel, date)
            return schedule

        shedules = self.harvestChannelSchedule(channel, date)
        if not shedules or len(shedules) == 0:
            log.warn('Failed channel schedule harvest: %s', channel)
            return None

        for schedule in shedules:
            date = datetime.strptime(schedule['date'], "%Y-%m-%d")
            shows = schedule['shows']
            if not self.hasChannelSchedule(channel, date):
                self.saveChannelSchedule(channel, date, shows)
            else:
                self.updateChannelSchedule(channel, date, shows)

        return shedules[0]['shows']

    def hasChannelSchedule(self, channel, date):
        log.debug('hasChannelSchedule(): %s (%s)', channel, date)
        return os.path.isfile(self.__getScheduleCache(channel, date))

    def listChannelSchedules(self, channel):
        log.debug('listChannelSchedules(): %s', channel)
        filesList = os.listdir(self.params.storage_dir)
        filePattern = re.compile("^" + channel + "\-(\d+)\.json")
        dates = []
        for fileName in filesList:
            match = filePattern.match(fileName)
            if not match:
                continue
            matchDate = match.group(1)
            log.debug('Found "%s" schedule at: %s', channel, matchDate)
            dates.append(datetime.strptime(matchDate, '%Y%m%d').date())

        return dates

    def readChannelSchedule(self, channel, date):
        log.debug('readChannelSchedule(): %s (%s)', channel, date)
        return readJson(self.__getScheduleCache(channel, date))

    def saveChannelSchedule(self, channel, date, schedule):
        log.debug('writeChannelSchedule(): %s (%s)', channel, date)
        return writeJson(self.__getScheduleCache(channel, date), schedule)

    def harvestChannelSchedule(self, channel, date):
        log.debug('harvestChannelSchedule(): %s (%s)', channel, date)
        if self.params.local_only:
            log.info('Found LOCAL_ONLY. Skipping harvest')
            return None

        channelsList = self.getChannelList()
        channelNumber = None
        channelName = None
        for channelData in channelsList:
            if channelData['name'] == channel or channelData['label'] == channel:
                # XXX(edzius): It could be simply just channelData['link']..?
                channelNumber = channelData['value']
                channelName = channelData['name']
                break

        if not channelName or not channelNumber:
            log.info('Missing channel metadata to start harvest')
            return

        log.info('Start channel schedule harvest "%s" (%s) date %s', channelName, channelNumber, date)
        if not date:
            guideUrl = self.SCHEDULE_URL_SELF % (channelName, channelNumber,)
        else:
            guideUrl = self.SCHEDULE_URL_DATE % (channelName, channelNumber, date.strftime("%Y_%m_%d"),)
        data = self.http.get(guideUrl)

        content = BeautifulSoup(data, 'html.parser')
        if not content:
            log.error('Failed parse: %s', guideUrl)
            self.http.archive()
            return

        # Attempt update channel list
        if not self.updateChannelList(content):
            log.debug('Failed attempt to update channel list')
            pass

        schedule = parseSchedule(content)
        if not schedule:
            log.error('Failed capture: %s', guideUrl)
            self.http.archive()
            return

        return schedule

    def readChannelList(self):
        log.debug('readChannelList()')
        return readJson(self.__getChannelsCache())

    def saveChannelList(self, channels):
        log.debug('saveChannelList()')
        return writeJson(self.__getChannelsCache(), channels)

    def harvestChannelList(self):
        log.debug('harvestChannelList()')
        if self.params.local_only:
            log.info('Found LOCAL_ONLY. Skipping harvest')
            return None

        log.info('Start channel list harvest')
        data = self.http.get(self.CHANNELS_URL)

        content = BeautifulSoup(data, 'html.parser')
        if not content:
            log.error('Failed parse: %s', url)
            self.http.archive()
            return

        channels = parseChannels(content)
        if not channels:
            log.error('Failed capture: %s', url)
            self.http.archive()
            return

        return channels

    def updateChannelList(self, channels):
        # TODO: Not required still
        return True

    def updateChannelSchedule(self, channel, date, guide):
        # TODO: Not required still
        return True
