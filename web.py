
import os
import shutil
import time
from datetime import datetime
import logging

log = logging.getLogger(__name__)


def download(url, destFile):
    command = 'wget -O %s "%s"' % (destFile, url,)
    log.debug('Execute wget command: "%s"', command)
    code = os.system(command)
    if code != 0:
        log.info("Failed wget, exit with code: %s", code)
        return

    try:
        log.debug('Read page contents, file: %s', destFile)
        f = open(destFile, 'r')
        data = f.read()
        f.close()
        return data
    except IOError as e:
        log.info('Failed read contens: %s', e.strerror)
        return


class Http:

    def __init__(self, params, cacheName=None):
        self.params = params
        self.cacheName = cacheName or (self.params.exec_name + ".data")
        self.cacheFile = os.path.join(self.params.cache_dir, self.cacheName)
        self.date = None

    def get(self, url):
        # Store get date for archiving
        self.date = datetime.now().strftime("%Y%m%d-%H%M%S")

        log.debug('Receiveing page contents of URL: %s', url)

        if self.params.delay:
            log.debug('Delay receive %s seconds', self.params.delay)
            time.sleep(self.params.delay)

        data = download(url, self.cacheFile)
        if not data:
            log.error('Failed download: "%s"', url)
            return

        log.debug('Finished page receive')

        return data

    def archive(self):
        log.debug('Archiving cache for inspection, date %s', self.date)
        if not os.path.exists(self.params.archive_dir):
            os.mkdir(self.params.archive_dir)

        archiveName = "%s-%s" % (self.date, self.cacheName,)
        archivePath = os.path.join(self.params.archive_dir, archiveName)
        try:
            shutil.copyfile(self.cacheFile, archivePath)
        except IOError as e:
            log.warn("archive failed: %s", e.strerror)

        log.info('Cache archived for inspection in: %s', archiveName)
