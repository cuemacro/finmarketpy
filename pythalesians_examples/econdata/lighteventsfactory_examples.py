__author__ = 'saeedamen'

#
# Copyright 2015 Thalesians Ltd. - http//www.thalesians.com / @thalesians
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and limitations under the License.
#

"""
lighteventsfactory_examples

Shows how to get detailed economic data. Note, that for the functions to work, you need to create your own HDF5
file filled with economic data (the format is detailed in LightEventsFactory file).

"""

from pythalesians.util.loggermanager import LoggerManager
from pythalesians.economics.events.lighteventsfactory import LightEventsFactory

#### Query economic data events database about various economic data events and print out findings
####
if True:
    logger = LoggerManager.getLogger(__name__)

    ef = LightEventsFactory()

    path = 'dump_econ.csv'
    ef.dump_economic_events_csv(path)

    logger.info("Output date/time for FOMC meetings")
    fomc_dates = ef.get_economic_event_date_time('USD', 'Federal Funds Target Rate - Upper Bound')

    logger.info(fomc_dates)

    logger.info("Output date/time for NFP events")
    nfp_dates = ef.get_economic_event_date_time('USD', 'US Employees on Nonfarm Payrolls Total MoM Net Change SA')

    logger.info(nfp_dates)

    logger.info("Output all event names in our database")
    events_names = ef.get_all_economic_events()

    logger.info(events_names)

    # logger.info("Output all date/time for events in our database")
    # event_times = ef.get_all_economic_events_date_time()

    logger.info("Output fields for NFP events: actual-release")
    fields = ['actual-release', 'survey-median']
    event_output = ef.get_economic_event_date_time_fields(fields=fields, name='USD', event='US Employees on Nonfarm Payrolls Total MoM Net Change SA')

    logger.info(event_output)

    logger.info("Output fields for AUD NFP events: actual-release")
    fields = ['actual-release', 'survey-median']
    event_output = ef.get_economic_event_date_time_fields(fields=fields, name='AUD', event='Australia Labor Force Employment Change SA')
    logger.info(event_output)

    logger.info("Output fields for AUD RBA events: actual-release")
    fields = ['actual-release', 'survey-median']
    event_output = ef.get_economic_event_date_time_fields(fields=fields, name='AUD', event='Australia RBA Cash Rate Target')

    logger.info(event_output)