######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import numpy as np
from unscented_transform import unscented_transform
from sigma_points import MerweSigmaPoints
from copy import deepcopy
from functools import partial


class UnscentedKFGRPC(object):
    """
    Implements the scaled Unscented Kalman filter (UKF)

    ====================================================================================================================

    Parameters

    dim_x : int, number of state variables for the filter.

    dim_y : int, number of of measurements.

    dt : float, time between steps in seconds.

    fx : function(x,dt), state transition function. dt is the time step in seconds.

    grpc_hx : grpc based measurement function. Transforms state vector x into a measurement vector of shape (dim_z).

    grpc_stub : grpc stub for the measurement model.

    ukf_params: list, contains ukf design parameters alpha, beta, kappa

    sigma_method : string, optional, refers to the method for computing the sigma points and weights of the UKF. Can be
                   either 'merwe' or 'julier'. 'merwe' implements the alpha, beta, kappa formulation of Van der Merwe.
                   'julier' implements Simon Julier's original kappa formulation. Default is 'merwe'.

    sqrt_method : string, optional, defines how the square root of a matrix, which has no unique answer, is computed.
                  Can be either 'chol' or 'sqrtm'. 'chol' implements the Cholesky formulation. The alternative is
                  scipy.linalg.sqrtm. Default is 'chol'.

    ====================================================================================================================

    Attributes

    x : numpy.array(dim_x), state estimate vector.

    P : numpy.array(dim_x, dim_x), covariance estimate matrix.

    x_pred : numpy.array(dim_x), predicted (prior) state estimate.

    P_pred : numpy.array(dim_x, dim_x), predicted (prior) state covariance matrix.

    x_updt : numpy.array(dim_x),  updated (posterior) state estimate.

    P_updt : numpy.array(dim_x, dim_x,  updated (posterior) state covariance matrix.

    y : ndarray, latest measurement used in update().

    Q : numpy.array(dim_x, dim_x), process noise covariance matrix.

    R : numpy.array(dim_z, dim_z), measurement noise covariance matrix.

    K : numpy.array, filter gain

    innov : numpy.array, innovation

    ====================================================================================================================

    """

    def __init__(self, dim_x, dim_y, fx, grpc_hx, ukf_params, grpc_stub, dt=None,  sigma_method=None, sqrt_method=None,
                 x_mean_fn=None, y_mean_fn=None, residual_x=None, residual_y=None, subtract=None):
        """
        :param dim_x: number of state variables for the filter.
        :param dim_y: number of of measurements.
        :param fx: state transition function. dt is the time step in seconds.
        :param grpc_hx: measurement function. Transforms state vector x into a measurement vector of shape (dim_z).
        :param dt: float, time between steps in seconds. Optional input.
        :param sigma_method: string, method for computing sigma points. Optional input
        :param sqrt_method: string, default is Cholesky. Optional input.
        """

        self.x = np.zeros(dim_x)
        self.P = np.eye(dim_x)
        self.x_pred = np.copy(self.x)
        self.P_pred = np.copy(self.P)
        self.Q = np.eye(dim_x)
        self.R = np.eye(dim_y)
        self._dim_x = dim_x
        self._dim_y = dim_y
        self._dt = dt
        self._index = 0
        self._sigma_method = sigma_method
        self._ukf_params = ukf_params
        self._subtract = subtract
        self.x_mean = x_mean_fn
        self.y_mean = y_mean_fn
        self.grpc_stub = grpc_stub

        if grpc_hx is None:
            raise RuntimeError("Measurement function is not defined. Please provide a valid function.")
        else:
            # self._hx = hx
            self._hx = partial(grpc_hx, self.grpc_stub)

        if fx is None:
            raise RuntimeError("State Transition function is not defined. Please provide a valid function.")
        else:
            self._fx = fx

        if sqrt_method is None or sqrt_method in ['chol', 'sqrtm']:
            self._sqrt_method = sqrt_method
        else:
            raise RuntimeError("Invalid method for computing matrix square root. Valid options are 'chol' or 'sqrtm'.")

        if sigma_method is None or sigma_method == 'merwe':
            sig_pts = MerweSigmaPoints(dim_x, ukf_params, sigma_method, sqrt_method, subtract)
            # weights for the means and covariances.
            self.sigma_points = sig_pts
            self.Wm, self.Wc = sig_pts.Wm, sig_pts.Wc
            self._num_sigmas = sig_pts.num_sigmas()
        else:
            raise RuntimeError("Invalid method for computing sigma points. Valid options are 'merwe' or 'julier'.")

        # sigma points transformed through f(x) and h(x). variables for efficiency so we don't recreate every update
        self.sigmas_f = np.zeros((self._num_sigmas, self._dim_x))
        self.sigmas_h = np.zeros((self._num_sigmas, self._dim_y))

        if residual_x is None:
            self.residual_x = np.subtract
        else:
            self.residual_x = residual_x

        if residual_y is None:
            self.residual_y = np.subtract
        else:
            self.residual_y = residual_y

        self.K = np.zeros((dim_x, dim_y))
        self.innov = np.zeros(dim_y)
        self.y = np.array([[None] * dim_y]).T

        self.S = np.zeros((dim_y, dim_y))  # system uncertainty
        self.SI = np.zeros((dim_y, dim_y))  # inverse system uncertainty
        self.inv = np.linalg.inv

        # these will always be a copy of x, P after predict() is called
        self.x_pred = self.x.copy()
        self.P_pred = self.P.copy()

        # these will always be a copy of x, P after update() is called
        self.x_updt = self.x.copy()
        self.P_updt = self.P.copy()

    def predict(self, **fx_args):
        r"""
        Performs the predict step of the UKF. On return, self.x and self. P contain the predicted state (x) and
        covariance (P). '

        Parameters
        ----------
        **fx_args : keyword arguments. optional keyword arguments to be passed into f(x).

        """
        # calculate sigma points for given mean and covariance
        self.compute_process_sigmas(**fx_args)

        # and pass sigmas through the unscented transform to compute prior
        self.x, self.P = unscented_transform(self.sigmas_f, self.Wm, self.Wc, self.Q, self.x_mean, self.residual_x)

        # save prior
        self.x_pred = np.copy(self.x)
        self.P_pred = np.copy(self.P)

    def update(self, y, **hx_args):
        """
        Update the UKF with the given measurements. On return, self.x and self.P contain the new mean and covariance
        of the filter.
        Parameters
        ----------
        y : numpy.array of shape (dim_y), measurement vector
        **hx_args : keyword argument. arguments to be passed into h(x) after x -> h(x, **hx_args)
        """

        if y is None:
            self.y = np.array([[None] * self._dim_y]).T
            self.x_updt = self.x.copy()
            self.P_updt = self.P.copy()
            return

        hx = self._hx

        if np.isscalar(self.R):
            R = np.eye(self._dim_y) * self.R
        else:
            R = self.R

        # pass prior sigmas through h(x) to get measurement sigmas, he shape of sigmas_h will vary if the shape of z
        # varies, so recreate each time
        sigmas_h = []
        for s in self.sigmas_f:
            sigmas_h.append(hx(s, **hx_args))

        self.sigmas_h = np.atleast_2d(sigmas_h)

        # mean and covariance of prediction passed through unscented transform
        yp, self.S = unscented_transform(self.sigmas_h, self.Wm, self.Wc, R, self.y_mean, self.residual_y)
        self.SI = self.inv(self.S)

        # compute cross variance of the state and the measurements
        Pxy = self.cross_variance(self.x, yp, self.sigmas_f, self.sigmas_h)

        self.K = np.dot(Pxy, self.SI)  # Kalman gain
        self.y = self.residual_y(y, yp)  # residual

        # update Gaussian state estimate (x, P)
        self.x = self.x + np.dot(self.K, self.y)
        self.P = self.P - np.dot(self.K, np.dot(self.S, self.K.T))

        # save measurement and posterior state
        self.y = deepcopy(y)
        self.x_updt = self.x.copy()
        self.P_updt = self.P.copy()

    def cross_variance(self, x, y, sigmas_f, sigmas_h):
        """
        Compute cross variance of the state `x` and measurement `y`.
        """

        Pxy = np.zeros((sigmas_f.shape[1], sigmas_h.shape[1]))
        N = sigmas_f.shape[0]
        for i in range(N):
            dx = self.residual_x(sigmas_f[i], x)
            dy = self.residual_y(sigmas_h[i], y)
            Pxy += self.Wc[i] * np.outer(dx, dy)
        return Pxy

    def compute_process_sigmas(self, **fx_args):
        """
        computes the values of sigmas_f. Normally a user would not call this, but it is useful if you need to call
        update more than once between calls to predict (to update for multiple simultaneous measurements), so the sigmas
        correctly reflect the updated state x, P.
        """

        fx = self._fx
        dt = self._dt

        # calculate sigma points for given mean and covariance
        sigmas = self.sigma_points.generate_sigmas(self.x, self.P)

        for i, s in enumerate(sigmas):
            self.sigmas_f[i] = fx(s, dt, **fx_args)
