# Project: finmarketpy project
# Filename: learn_network_structure
# Objective: compute a network graph for a group of asset return time series
# Created: 2019-11-02 12:05
# Version: 0.0
# Author: FS

__author__ = 'fs'

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

import numpy as np
from sklearn import cluster, covariance, manifold


def learn_network_structure(ts_returns_data, names, alphas=4, cv=5, mode='cd',
							assume_centered = False,
							n_components=2, n_neighbors=5,
							eigen_solver="dense", method='standard',
							neighbors_algorithm="auto",
							random_state = None, n_jobs=None,
							standardise=False):
	"""

	Parameters
	----------
	ts_returns_data : array-like of shape [n_samples, n_instruments]
	                  time series matrix of returns

	names : array-like of shape [n_samples, 1]
	        Individual names of the financial instrument

	alphas : int or positive float, optional
	         Number of points on the grids to be used

	cv : int, optional
	     Number of folds for cross-validation splitting strategy

	mode : str, optional
	       Solver to use to compute the graph

	assume_centered : bool, optional
                      Centre the data if False.

	n_components : int
	               Number of components for the manifold

	n_neighbors: int
                 Number of neighbours to consider for each point

	eigen_solver : str
	               Algorithm to compute eigenvalues

	method : str
             Algorithm to use for local linear embedding
	neighbors_algorithm : str
	                      Algorithm to use for nearest neighbours search

	random_state : int, RandomState instance or None, optional
	               If int, random_state is the seed used by the random number generator.
	               If RandomState instance, random_state is the random number generator.
	               If None, the random number generator is the RandomState instance used by np.random.
	               Used when eigen_solver == ‘arpack’

	n_jobs : int or None, optional
	         number of parallel jobs to run

	standardise : bool
	              standardise data if True

	Returns : sklearn.covariance.graph_lasso_.GraphicalLassoCV

              sklearn.manifold.locally_linear.LocallyLinearEmbedding

              array-like of shape [n_components, n_instruments]
              Transformed embedding vectors

              array-like of shape [n_instruments, 1]
              numeric identifier of each cluster



	-------
	"""

	if not isinstance(ts_returns_data, (np.ndarray, np.generic)):
		raise TypeError("ts_returns_data must be of class ndarray")

	# learn graphical structure
	edge_model = covariance.GraphicalLassoCV(alphas=alphas, cv=cv, mode=mode,
											 assume_centered=assume_centered)
	edge_model.fit(ts_returns_data)

	# cluster using affinity propagation
	_, labels = cluster.affinity_propagation(edge_model.covariance_)
	n_labels = labels.max()
	for i in range(n_labels + 1):
		print('Cluster %i: %s' % ((i + 1), ', '.join(names[labels == i])))

	# find low-dimension embedding - useful for 2D plane visualisation
	node_position_model = manifold.LocallyLinearEmbedding(
			n_components=n_components, eigen_solver=eigen_solver,
			n_neighbors=n_neighbors, method=method,
			neighbors_algorithm=neighbors_algorithm,
			random_state=random_state, n_jobs=n_jobs)
	embedding = node_position_model.fit_transform(ts_returns_data.T).T

	if standardise:
		# standardise returns
		standard_ret = ts_returns_data.copy()
		standard_ret /= ts_returns_data.std(axis=0)

		# learn graph model
		edge_model.fit(standard_ret)

		# cluster using affinity propagation
		_, labels = cluster.affinity_propagation(edge_model.covariance_)
		n_labels = labels.max()
		for i in range(n_labels + 1):
			print('Cluster %i: %s' % ((i + 1), ', '.join(names[labels == i])))

		# find low-dimension embedding - useful for 2D plane visualisation
		node_position_model = manifold.LocallyLinearEmbedding(
				n_components=n_components, eigen_solver=eigen_solver,
				n_neighbors=n_neighbors, method=method,
				neighbors_algorithm=neighbors_algorithm,
				random_state=random_state, n_jobs=n_jobs)
		embedding = node_position_model.fit_transform(ts_returns_data.T).T

	return edge_model, node_position_model, embedding, labels
