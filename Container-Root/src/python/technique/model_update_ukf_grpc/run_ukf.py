######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import sys
import numpy as np
from ukf_utils import initialize_ukf


# Execute an UKF based model update and return update model parameter values
# and covariance
def run_ukf(grpc_stub, ukf_input_dict):
    ukf = initialize_ukf(ukf_input_dict, grpc_stub)
    print('Initial State after UKF initialization', ukf.x)
    out_var = dict()
    out_var['input_dict'] = ukf_input_dict
    out_var_names = list(ukf_input_dict['analyticSettings']['model']['outputs']['actual'].keys())
    num_vars = len(out_var_names)
    num_pts = len(ukf_input_dict['analyticSettings']['model']['outputs']['actual'][out_var_names[0]])
    y_act = np.ones((num_pts, num_vars)) * np.nan
    for indx, var_name in enumerate(out_var_names):
        y_act[:, indx] = np.array(ukf_input_dict['analyticSettings']['model']['outputs']['actual'][var_name])

    y_act = y_act.flatten()

    # Run iterative UKF to update the model
    print('Starting Iterative UKF update')
    for iter in np.arange(0, ukf.max_iter):
        print('Iteration: ', iter + 1)
        print('Initial State at this iteration', ukf.x)
        ukf.predict()
        ukf.update(y_act, **out_var)
        print('Updated State at this iteration', ukf.x)
        print()

    # Compose the tunable Params dict back
    tunable_params = dict()
    tunable_params_cov = dict()
    cur_idx = 0
    tunable_params_cov['P'] = ukf.P.tolist()
    for cur_tuple in ukf.x_name_len_list:
        cur_name = cur_tuple[0]
        cur_len = cur_tuple[1]
        tunable_params[cur_name] = ukf.x[cur_idx:cur_idx+cur_len].tolist()
        cur_idx += cur_len

    return tunable_params, tunable_params_cov