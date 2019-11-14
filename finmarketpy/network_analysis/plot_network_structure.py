# Project: finmarketpy project
# Filename: plot_network_structure
# Objective:
# Created: 2019-11-02 17:38
# Version: 0.0
# Author: FS

# importing packages
import numpy as np
from sklearn import covariance
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection


def plot_network_structure(
    edge_model,
    embedding,
    names,
    labels,
    ax=[0.0, 0.0, 1.0, 1.0],
    figsize=None,
    corr_threshold=0.02,
    vmin=0,
    vmax=0.5,
    lw=1,
    alpha=None,
    cmap_scatter=plt.cm.nipy_spectral,
    cmap_lc=plt.cm.hot_r,
    edgecolor=plt.cm.nipy_spectral,
):
    """

    Parameters
    ----------
    edge_model: sklearn.covariance.graph_lasso_.GraphicalLassoCV
                The model specifications to build the graph

    embedding: array-like of shape [n_components, n_instruments]
               Transformed embedding vectors

    names: array-like of shape [n_samples, 1]
           Names of each financial instrument

    labels: array-like of shape [n_instruments, 1]
            numeric identifier of each cluster
    ax: list of of 4 floats [left, bottom, width, height]
        Add an axes to the current figure and make it the current axes (plt.axes
        official docs)

    figsize: (float, float), optional, default: None
             Width and height in inches

    corr_threshold: float
                    Minimum correlation value for which to display points
    vmin: float
          Minimum value allowed in the normalised range

    vmax: float
          Maximum value allowed in the normalised range

    lw: float or sequence of float

    alpha: float between 0 and 1
           Degree of transparency of the plot

    cmap_scatter: plt.cm
                  colour-mapping for scatter plots
    cmap_lc: plt.cm
             colour-mapping for LineCollection

    edgecolor: plt.cm
               colour of the borders of the box containing each financial instrument
               name

    Returns
    A plot representing the correlation network of the financial instruments
    -------

    """
    if not isinstance(edge_model, covariance.graph_lasso_.GraphicalLassoCV):
        raise TypeError(
            "edge_model must be of class "
            "covariance.graph_lasso_"
            ".GraphicalLassoCV "
        )

    if not isinstance(embedding, (np.ndarray, np.generic)):
        raise TypeError("embedding must be of class ndarray.")

    plt.figure(1, facecolor="w", figsize=figsize)
    plt.clf()
    ax = plt.axes(ax)
    plt.axis("off")

    # display a graph of the partial correlations
    partial_correlations = edge_model.precision_.copy()
    d = 1 / np.sqrt(np.diag(partial_correlations))
    partial_correlations *= d
    partial_correlations *= d[:, np.newaxis]
    non_zero = np.abs(np.triu(partial_correlations, k=1)) > corr_threshold

    # plot the nodes using the coordinates in embedding
    plt.scatter(embedding[0], embedding[1], s=100 * d ** 2, c=labels, cmap=cmap_scatter)

    # plot the edges
    start_idx, end_idx = np.where(non_zero)
    segments = [
        [embedding[:, start], embedding[:, stop]]
        for start, stop in zip(start_idx, end_idx)
    ]
    corr_values = np.abs(partial_correlations[non_zero])
    lc = LineCollection(
        segments,
        zorder=0,
        cmap=cmap_lc,
        norm=plt.Normalize(vmin=vmin, vmax=vmax * corr_values.max()),
    )
    lc.set_array(corr_values)
    lc.set_linewidth(lw=lw * corr_values)
    ax.add_collection(lc)

    # add a label to each node
    n_labels = labels.max()
    for index, (name, label, (x, y)) in enumerate(zip(names, labels, embedding.T)):

        dx = x - embedding[0]
        dx[index] = 1
        dy = y - embedding[1]
        dy[index] = 1
        this_dx = dx[np.argmin(np.abs(dy))]
        this_dy = dy[np.argmin(np.abs(dx))]
        if this_dx > 0:
            horizontalalignment = "left"
            x = x + 0.002
        else:
            horizontalalignment = "right"
            x = x - 0.002
        if this_dy > 0:
            verticalalignment = "bottom"
            y = y + 0.002
        else:
            verticalalignment = "top"
            y = y - 0.002
        plt.text(
            x,
            y,
            name,
            size=10,
            horizontalalignment=horizontalalignment,
            verticalalignment=verticalalignment,
            bbox=dict(
                facecolor="w", edgecolor=edgecolor(label / float(n_labels)), alpha=alpha
            ),
        )

        plt.xlim(
            embedding[0].min() - 0.15 * embedding[0].ptp(),
            embedding[0].max() + 0.10 * embedding[0].ptp(),
        )
        plt.ylim(
            embedding[1].min() - 0.03 * embedding[1].ptp(),
            embedding[1].min() + 0.03 * embedding[1].ptp(),
        )

        plt.show()
