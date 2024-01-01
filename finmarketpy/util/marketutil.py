__author__ = 'saeedamen'  # Saeed Amen

#
# Copyright 2016-2020 Cuemacro - https://www.cuemacro.com / @cuemacro
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and limitations under the License.
#

import datetime
from datetime import timedelta

import pandas as pd

class MarketUtil(object):

    def parse_date(self, date):
        if isinstance(date, str):

            date1 = datetime.datetime.utcnow()

            if date == "midnight":
                date1 = datetime.datetime(date1.year, date1.month, date1.day, 0, 0, 0)
            elif date == "decade":
                date1 = date1 - timedelta(days=365 * 10)
            elif date == "year":
                date1 = date1 - timedelta(days=365)
            elif date == "month":
                date1 = date1 - timedelta(days=30)
            elif date == "week":
                date1 = date1 - timedelta(days=7)
            elif date == "day":
                date1 = date1 - timedelta(days=1)
            elif date == "hour":
                date1 = date1 - timedelta(hours=1)
            else:
                # format expected 'Jun 1 2005 01:33', '%b %d %Y %H:%M'
                try:
                    date1 = datetime.datetime.strptime(date, '%b %d %Y %H:%M')
                except:
                    # ogger.warning("Attempted to parse date")
                    i = 0

                # format expected '1 Jun 2005 01:33', '%d %b %Y %H:%M'
                try:
                    date1 = datetime.datetime.strptime(date, '%d %b %Y %H:%M')
                except:
                    # logger.warning("Attempted to parse date")
                    i = 0

                try:
                    date1 = datetime.datetime.strptime(date, '%b %d %Y')
                except:
                    # logger.warning("Attempted to parse date")
                    i = 0

                try:
                    date1 = datetime.datetime.strptime(date, '%d %b %Y')
                except:
                    # logger.warning("Attempted to parse date")
                    i = 0
        else:
            date1 = pd.Timestamp(date)

        return pd.Timestamp(date1)