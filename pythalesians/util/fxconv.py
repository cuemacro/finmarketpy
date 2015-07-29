__author__ = 'saeedamen' # Saeed Amen / saeed@pythalesians.com

#
# Copyright 2015 Thalesians Ltd. - http//www.pythalesians.com / @pythalesians
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
FXConv

Various helper methods to manipulate FX crosses, applying correct conventions.

"""

from pythalesians.util.loggermanager import LoggerManager

class FXConv:

    # TODO
    g10 = ['EUR', 'GBP', 'AUD', 'NZD', 'USD', 'CAD', 'CHF', 'NOK', 'SEK', 'JPY']
    order = ['XAU', 'XPT', 'XBT', 'XAG', 'EUR', 'GBP', 'AUD', 'NZD', 'USD', 'CAD', 'CHF', 'NOK', 'SEK', 'JPY']

    def __init__(self):
        self.logger = LoggerManager().getLogger(__name__)
        return

    def g10_crosses(self):

        g10_crosses = []

        for i in range(0, len(self.g10)):
            for j in range(0, len(self.g10)):
                if i != j:
                    g10_crosses.append(self.correct_notation(self.g10[i] + self.g10[j]))

        set_val = set(g10_crosses)
        g10_crosses = sorted(list(set_val))

        return g10_crosses

    def em_or_g10(self, currency, freq = "daily"):
        if freq == 'intraday':
            return 'fx'

        try:
            index = self.g10.index(currency)
        except ValueError:
            index = -1

        if (index < 0):
            return 'fx-em'

        return 'fx-g10'

    def is_USD_base(self, cross):
        base = cross[0:3]
        terms = cross[3:6]

        if base == 'USD':
            return True

        return False

    def is_EM_cross(self, cross):
        base = cross[0:3]
        terms = cross[3:6]

        if self.em_or_g10(base, 'daily') == 'fx-em' or self.em_or_g10(terms, 'daily') == 'fx-em':
            return True

        return False

    def correct_notation(self, cross):
        base = cross[0:3]
        terms = cross[3:6]

        try:
            base_index = self.order.index(base)
        except ValueError:
            base_index = -1

        try:
            terms_index = self.order.index(terms)
        except ValueError:
            terms_index = -1

        if (base_index < 0 and terms_index > 0):
            return terms + base
        if (base_index > 0 and terms_index < 0):
            return base + terms
        elif (base_index > terms_index):
            return terms + base
        elif (terms_index > base_index):
            return base + terms

        return cross

if __name__ == '__main__':
    logger = LoggerManager.getLogger(__name__)

    fxconv = FXConv()

    if True:
        logger.info(fxconv.g10_crosses())
