
import collections
import datetime
import logging

log = logging.getLogger(__name__)


def getChannelsList(sotre, channels=None):
    log.debug('getChannelsList()')
    channels = channels or store.getChannelList()
    return map(lambda channel: channel['name'], channels)

def getGroupsList(store, channels=None):
    log.debug('getGroupList()')
    def reduceList(array, element):
        if element['group'] not in array:
            array.append(element['group'])
        return array
    channels = channels or store.getChannelList()
    return reduce(reduceList, channels, [])

def getChannelsMap(store):
    log.debug('getChannnelsMap()')
    result = collections.OrderedDict()
    for channel in store.getChannelList():
        result[channel['name']] = channel['label']
    return result

def getCategoriesMap(store):
    log.debug('getCategoriesMap()')
    result = collections.OrderedDict()
    for channel in store.getChannelList():
        result[channel['group']] = channel['category']
    return result

def enlist(item):
    if type(item) == str:
        return [item]
    elif type(item) == list:
        return item

def timeCompare(time1, time2):
    def swap(v1, v2):
        return v2, v1

    time1delta = time1.hour - 12
    time2delta = time2.hour - 12
    if abs(time1delta - time2delta) >= 12:
        time1, time2 = swap(time1, time2)

    if time1 > time2:
        return 1
    elif time1 < time2:
        return -1
    else:
        return 0


class ShowSelect:

    def __init__(self, store, force=False):
        self.store = store
        self.force = force

    def __listChannelNames(self, channels=None):
        return getChannelsList(self.store, channels)

    def __listChannelGroups(self, channels=None):
        return getGroupsList(self.store, channels)

    ##
    # Format channel names list according provided chName or chGroup
    ##
    def __formatChannelList(self, channelsList, chName=None, chGroup=None):
        if chName:
            log.debug('__formatChannelList(): single channel filter %s', chName)
            channelsAll = self.__listChannelNames(channelsList)
            # TODO(edzius): add debug logging for filtered channels
            channels = filter(lambda channel: channel in channelsAll, enlist(chName))
        elif chGroup:
            log.debug('__formatChannelList(): channel group filter %s', chGroup)
            groupsAll = self.__listChannelGroups(channelsList)
            # TODO(edzius): add debug logging for filtered channels. Otherwise this filter is redundant
            groups = filter(lambda group: group in groupsAll, enlist(chGroup))
            channels = self.__listChannelNames(filter(lambda channel: channel['group'] in groups, channelsList))
            log.debug('__formatChannelList(): channel group found channels %s', channels)
        else:
            log.debug('__formatChannelList(): all channel filter')
            channels = self.__listChannelNames(channelsList)

        return channels

    ##
    # Format channels matrix according provided date or dateFrom and dateTo
    ##
    def __formatChannelTimetable(self, channelsList, date=None, dateFrom=None, dateTo=None):
        channelsMatrix = {}
        # FIXME(edzius): Channel names in list as IS. Fix to convert to std from.
        if date != None:
            log.debug('__formatChannelTimetable(): single date mapping %s', date)
            channelsMatrix[date] = list(channelsList)
        elif dateFrom != None and dateTo != None:
            log.debug('__formatChannelTimetable(): range dates mapping %s - %s', dateFrom, dateTo)
            day = datetime.timedelta(days=1)
            while dateFrom <= dateTo:
                log.debug('__formatChannelTimetable(): add range date mapping %s', dateFrom)
                channelsMatrix[dateFrom] = list(channelsList)
                dateFrom += day
        else:
            log.debug('__formatChannelTimetable(): use cached channel dates')
            for channel in channelsList:
                log.debug('__formatChannelTimetable(): lookuop channel schedules for %s', channel)
                chSchedules = self.store.listChannelSchedules(channel)
                for chDate in chSchedules:
                    log.debug('__formatChannelTimetable(): include channel schedule %s for %s', chDate, channel)
                    if chDate not in channelsMatrix:
                        channelsMatrix[chDate] = []
                    channelsMatrix[chDate].append(channel)

        return channelsMatrix

    def __formatShowsList(self, channel, showsList, showName=None, time=None, timeFrom=None, timeTo=None):
        log.debug('__formatShowsList(): %s showName=%s time=%s timeFrom=%s timeTo=%s', channel, showName, time, timeFrom, timeTo)
        nowTime = datetime.datetime.now().time()
        timeThis = None
        timeNext = None
        shows = []
        for i in range(len(showsList)):
            show = showsList[i]
            if showName and show['title'].find(showName) == -1 and show['description'].find(showName) == -1:
                log.debug('FILTER: Not satisfied show title/description (%s/%s): %s', show['title'], show['description'], showName)
                continue

            if i+1 < len(showsList):
                showNext = showsList[i+1]
            else:
                showNext = showsList[0]
            # Optimization for date parsing
            timeThis = timeNext or datetime.datetime.strptime(show['time'], '%H:%M').time()
            timeNext = datetime.datetime.strptime(showNext['time'], "%H:%M").time()
            if time != None:
                if timeCompare(time, timeThis) < 0 or timeCompare(time, timeNext) >= 0:
                    log.debug('FILTER: Not satisfied show time (%s-%s): %s', timeThis, timeNext, time)
                    continue
            if timeFrom != None:
                if timeCompare(timeFrom, timeNext) > 0:
                    log.debug('FILTER: Not satisfied show time (%s): more %s', timeNext, timeFrom)
                    continue
            if timeTo != None:
                if timeCompare(timeTo, timeThis) < 0:
                    log.debug('FILTER: Not satisfied show timeTo (%s): less %s', timeThis, timeTo)
                    continue

            show['live'] = (timeCompare(nowTime, timeThis) >= 0 and timeCompare(nowTime, timeNext) < 0)
            show['ends'] = showNext['time']
            show['channel'] = channel
            shows.append(show)

        return shows

    def select(self, chName=None, chGroup=None, showName=None, date=None, dateFrom=None, dateTo=None, time=None, timeFrom=None, timeTo=None):
        log.debug('select(): chName=%s chGroup=%s showName=%s date=%s dateFrom=%s dateTo=%s time=%s timeFrom=%s timeTo=%s', 
                  chName, chGroup, showName, date, dateFrom, dateTo, time, timeFrom, timeTo)
        channelsList = self.store.getChannelList()
        selectedChannels = self.__formatChannelList(channelsList, chName, chGroup)
        selectedTimetable = self.__formatChannelTimetable(selectedChannels, date, dateFrom, dateTo)

        selectedResult = []
        for date, channels in selectedTimetable.items():
            for channel in channels:
                channelShows = self.store.getChannelSchedule(channel, date)
                if not channelShows:
                    log.info('No shows for channel %s', channel)
                    continue

                selectedShows = self.__formatShowsList(channel, channelShows, showName, time, timeFrom, timeTo)
                if len(selectedShows) == 0:
                    log.debug('No criteria matchinf shows for channel %s', channel)
                    continue

                selectedResult.extend(selectedShows)

        log.debug('Selected shows matching criteria: %s', len(selectedResult))

        return selectedResult
