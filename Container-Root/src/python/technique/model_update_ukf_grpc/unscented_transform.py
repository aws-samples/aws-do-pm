######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import numpy as np

def unscented_transform(sigmas, w_mean, w_cov, noise_cov=None, mean_fn=None, residual_fn=None):
    """
    Computes unscented transform of a set of sigma points and weights. returns the mean and covariance in a tuple.
    This works in conjunction with the UnscentedKF class.

    Parameters
    ----------
    sigmas: ndarray, of size (n, 2n+1), 2D array of sigma points.

    w_mean : ndarray [# sigmas per dimension], Weights for the mean.

    w_cov : ndarray [# sigmas per dimension], Weights for the covariance.

    noise_cov : ndarray, optional, noise matrix added to the final computed covariance matrix.

    mean_fn : callable (sigma_points, weights), optional

    residual_fn : callable (x, y)

    Returns
    -------
    x : ndarray [dimension], Mean of the sigma points after passing through the transform.

    P : ndarray, covariance of the sigma points after passing throgh the transform.

    """

    num_sig, num_st = sigmas.shape
    if mean_fn is None:
        # new mean is just the sum of the sigmas * weight
        x = np.dot(w_mean, sigmas)    # dot = \Sigma^n_1 (W[k]*Xi[k])
    else:
        x = mean_fn(sigmas, w_mean)

    # new covariance is the sum of the outer product of the residuals times the weights
    if residual_fn is np.subtract or residual_fn is None:
        y = sigmas - x[np.newaxis, :]
        P = np.dot(y.T, np.dot(np.diag(w_cov), y))
    else:
        P = np.zeros((num_st, num_st))
        for k in range(num_sig):
            y = residual_fn(sigmas[k], x)
            P += w_cov[k] * np.outer(y, y)

    if noise_cov is not None:
        P += noise_cov

    return x, P
