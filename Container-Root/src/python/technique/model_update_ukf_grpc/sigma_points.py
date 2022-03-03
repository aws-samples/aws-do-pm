######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import numpy as np
from scipy.linalg import cholesky, sqrtm


class MerweSigmaPoints(object):

    """
    Generates sigma points and weights according to the alpha, beta, kappa formulation of Van der Merwe.

    Parameters
    ----------
    n : int, dimensionality of the state. 2n+1 weights will be generated.

    ukf_params: parameters for computing sigma points

    sigma_method: string, method for computing sigma points

    sqrt_method : string, determines how the square root of a matrix is calculated.

    subtract : callable (x, y), optional, function that computes the difference between x and y.

    Attributes
    ----------
    Wm : np.array, weight for each sigma point for the mean
    Wc : np.array, weight for each sigma point for the covariance
    """

    def __init__(self, n, ukf_params, sigma_method=None, sqrt_method=None, subtract=None):

        self.n = n

        if sigma_method is None or sigma_method == 'merwe':
            self.alpha = ukf_params[0]
            self.beta = ukf_params[1]
            self.kappa = ukf_params[2]
        elif sqrt_method == 'julier':
            self.kappa = ukf_params[0]
        else:
            raise RuntimeError("Invalid method for computing sigma points. Valid options are 'merwe' or 'julier'.")

        if sqrt_method is None or sqrt_method == 'chol':
            self.msqrt = cholesky
        elif sqrt_method == 'sqrtm':
            self.msqrt = sqrtm
        else:
            raise RuntimeError("Invalid method for computing matrix square root. Valid options are 'chol' or 'sqrtm'.")

        if subtract is None:
            self.subtract = np.subtract
        else:
            self.subtract = subtract

        self._compute_weights()

    def num_sigmas(self):
        """ Number of sigma points for each variable in the state x"""

        return 2*self.n + 1

    def generate_sigmas(self, x, P):
        """
        Computes the sigma points for an unscented Kalman filter given the mean (x) and covariance(P) of the filter.
        Returns tuple of the sigma points and weights.

        Returns
        -------
        sigmas : np.array, of size (n, 2n+1), Two dimensional array of sigma points. Each column contains all of the
                sigmas for one dimension in the problem space. Ordered by Xi_0, Xi_{1..n}, Xi_{n+1..2n}.
        """

        if self.n != np.size(x):
            raise ValueError("expected size(x) {}, but size is {}".format(self.n, np.size(x)))

        n = self.n

        if np.isscalar(x):
            x = np.asarray([x])

        if np.isscalar(P):
            P = np.eye(n)*P
        else:
            P = np.atleast_2d(P)

        lambda_ = self.alpha**2 * (n + self.kappa) - n
        sqrt_P = self.msqrt((lambda_ + n)*P)

        sigmas = np.zeros((2*n+1, n))
        sigmas[0] = x
        for k in range(n):
            sigmas[k+1] = self.subtract(x, -sqrt_P[k])
            sigmas[n+k+1] = self.subtract(x, sqrt_P[k])

        return sigmas

    def _compute_weights(self):
        """ Computes the weights for the scaled unscented Kalman filter.
        """
        n = self.n
        lambda_ = self.alpha ** 2 * (n + self.kappa) - n
        c = .5 / (n + lambda_)
        self.Wc = np.full(2 * n + 1, c)
        self.Wm = np.full(2 * n + 1, c)
        self.Wc[0] = lambda_ / (n + lambda_) + (1 - self.alpha ** 2 + self.beta)
        self.Wm[0] = lambda_ / (n + lambda_)
