__author__ = 'saeedamen'

from pythalesians.util.loggermanager import LoggerManager
from pythalesians.economics.events.histecondatafactory import HistEconDataFactory
from pythalesians.economics.events.popular.commonecondatafactory import CommonEconDataFactory

import datetime

class EconComparison:
        pass

if __name__ == '__main__':
    logger = LoggerManager.getLogger(__name__)

    hist = HistEconDataFactory()
    start_date = '01 Jan 1990'
    finish_date = datetime.datetime.utcnow()