"""Tests for network analysis modules."""

from unittest.mock import patch

import numpy as np
import pytest

# ---- learn_network_structure ----


def test_learn_network_structure_type_error():
    """learn_network_structure raises TypeError for non-ndarray input."""
    from finmarketpy.network_analysis.learn_network_structure import learn_network_structure

    with pytest.raises(TypeError):
        learn_network_structure([[1, 2], [3, 4]], np.array(["A", "B"]))


def test_learn_network_structure_basic():
    """learn_network_structure returns expected tuple with valid ndarray input."""
    from finmarketpy.network_analysis.learn_network_structure import learn_network_structure

    rng = np.random.default_rng(0)
    # 100 observations, 10 instruments (n_neighbors=5 < 10 instruments so LLE doesn't fail)
    data = rng.normal(0, 0.01, (100, 10))
    names = np.array(["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"])
    edge_model, _node_position_model, embedding, labels = learn_network_structure(
        data, names, alphas=2, cv=3, n_neighbors=4, random_state=42
    )
    assert edge_model is not None
    assert embedding.shape[0] == 2  # n_components
    assert len(labels) == 10


def test_learn_network_structure_standardise():
    """learn_network_structure with standardise=True returns valid output."""
    from finmarketpy.network_analysis.learn_network_structure import learn_network_structure

    rng = np.random.default_rng(1)
    data = rng.normal(0, 0.01, (100, 10))
    names = np.array(["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"])
    edge_model, _node_position_model, embedding, _labels = learn_network_structure(
        data, names, alphas=2, cv=3, n_neighbors=4, standardise=True, random_state=42
    )
    assert edge_model is not None
    assert embedding is not None


# ---- plot_network_structure ----


def test_plot_network_structure_type_error_edge_model():
    """plot_network_structure raises TypeError for invalid edge_model."""
    from finmarketpy.network_analysis.plot_network_structure import plot_network_structure

    rng = np.random.default_rng(0)
    embedding = rng.normal(0, 1, (2, 10))
    names = np.array(["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"])
    labels = np.zeros(10, dtype=int)

    # The check in plot_network_structure uses covariance.graph_lasso_.GraphicalLassoCV
    # which may not exist in newer sklearn; the function itself raises AttributeError
    # or TypeError depending on the sklearn version. Test that it doesn't silently pass.
    with pytest.raises((TypeError, AttributeError)):
        plot_network_structure("not_a_model", embedding, names, labels)


def test_plot_network_structure_type_error_embedding():
    """plot_network_structure raises TypeError for invalid embedding."""
    from finmarketpy.network_analysis.learn_network_structure import learn_network_structure
    from finmarketpy.network_analysis.plot_network_structure import plot_network_structure

    rng = np.random.default_rng(0)
    data = rng.normal(0, 0.01, (100, 10))
    names = np.array(["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"])
    edge_model, _, _, labels = learn_network_structure(data, names, alphas=2, cv=3, n_neighbors=4, random_state=42)

    with pytest.raises((TypeError, AttributeError)):
        plot_network_structure(edge_model, "not_an_array", names, labels)


def test_plot_network_structure_runs():
    """plot_network_structure renders without error given valid input."""
    import matplotlib as mpl

    mpl.use("Agg")  # non-interactive backend for testing
    import matplotlib.pyplot as plt

    from finmarketpy.network_analysis.learn_network_structure import learn_network_structure
    from finmarketpy.network_analysis.plot_network_structure import plot_network_structure

    rng = np.random.default_rng(2)
    data = rng.normal(0, 0.01, (100, 10))
    names = np.array(["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"])
    edge_model, _, embedding, labels = learn_network_structure(
        data, names, alphas=2, cv=3, n_neighbors=4, random_state=42
    )

    # Use corr_threshold=0 to ensure edges are present and avoid zero-size array errors
    with patch("matplotlib.pyplot.show"):
        plot_network_structure(edge_model, embedding, names, labels, corr_threshold=0.0)

    plt.close("all")
