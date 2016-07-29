__author__ = 'saeedamen'

import seaborn as sns

from pythalesians_graphics.graphs.lowleveladapters.adapterpythalesians import AdapterPyThalesians
from pythalesians_graphics.graphs.graphproperties import GraphProperties

class AdapterSeaborn(AdapterPyThalesians):

    def plot_2d_graph(self, data_frame, gp, chart_type):
        sns.set()

        if gp is None: gp = GraphProperties()
        if gp.chart_type is None and chart_type is None: chart_type = 'line'

        if gp.resample is not None: data_frame = data_frame.asfreq(gp.resample)

        self.apply_style_sheet(gp)

        if chart_type == 'heatmap':
            # Draw a heatmap with the numeric values in each cell
            sns_plot = sns.heatmap(data_frame, annot=True, fmt="d", linewidths=.5)

            fig = sns_plot.fig

        # TODO
        pass