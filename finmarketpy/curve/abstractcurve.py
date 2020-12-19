__author__ = 'saeedamen' # Saeed Amen / saeed@cuemacro.com

#
# Copyright 2020 Cuemacro Ltd. - http//www.cuemacro.com / @cuemacro
#
# See the License for the specific language governing permissions and limitations under the License.
#
# This may not be distributed without the permission of Cuemacro.
#

import abc

class AbstractCurve(object):
    """Abstract class for creating indices and curves, which is for example implemented by FXSpotCurve and could be implemented
    by other asset classes.

    """

    @abc.abstractmethod
    def generate_key(self):
        return

    @abc.abstractmethod
    def fetch_continuous_time_series(self, md_request, market_data_generator):
        return

    @abc.abstractmethod
    def construct_total_returns_index(self):
        return
