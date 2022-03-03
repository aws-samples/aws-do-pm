######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################


# This file contains helper functions required for implementing the UKF based
# model update.

import sys
sys.path.append("/app/grpc_compiled")
from grpc_compiled import model_interface_pb2, model_interface_pb2_grpc
from unscented_kf_grpc import UnscentedKFGRPC
from lib.util.encode_decode_json import utf_encode_json, utf_decode_json
import numpy as np
import pandas as pd


# Helper function for getting UKF parameters from input dictionary
def get_ukf_params(ukf_input_dict):
    ukf_params = dict()
    ukf_param_names = ukf_input_dict['analyticSettings']['ukf'].keys()
    for name in ukf_param_names:
        ukf_params[name] = ukf_input_dict['analyticSettings']['ukf'][name]
    return ukf_params


# This is the grpc based output function of the UKF. The model (measurement equation of the UKF)
# is evaluated with inputs and sigma points.
def grpc_hx(grpc_stub, x, input_dict):
    model_dict = input_dict['analyticSettings']['model']
    # set state in the model_dict
    tunable_param_names = list(model_dict['analyticSettings']['tunableParams'].keys())

    count = 0
    for indx, name in enumerate(tunable_param_names):
        this_param_length = len(model_dict['analyticSettings']['tunableParams'][name])

        this_var_list = list()
        for idx in np.arange(count, count+this_param_length):
            this_var_list.append(x[idx])
        count = count + this_param_length
        model_dict['analyticSettings']['tunableParams'][name] = this_var_list

    model_dict_encoded = utf_encode_json(model_dict)
    query = model_interface_pb2.inRequest(inp_dict_bytes=model_dict_encoded)
    response = grpc_stub.EvaluateModel(query)
    response_dict = utf_decode_json(response.response_bytes)

    # Convert to dataframe and print the contents
    res_pd = pd.DataFrame.from_dict(response_dict['prediction'])
    y_pred = list()

    # Get model output variable names
    model_output_names = list(model_dict['outputs']['actual'].keys())
    for indx, name in enumerate(model_output_names):
        y_pred.append(res_pd[name].values)
    y_pred = np.array(y_pred).transpose()
    y_pred = y_pred.flatten()
    return y_pred


# UKF process function.
def fx(x, dt):
    # Nothing to do here. Process Model is random walk
    return x


# Intialize the UKF object
def initialize_ukf(ukf_input_dict, grpc_stub):
    ukf_settings = get_ukf_params(ukf_input_dict)
    model_dict = ukf_input_dict['analyticSettings']['model']

    # set state in the model_dict
    tunable_param_names = list(model_dict['analyticSettings']['tunableParams'].keys())
    out_var_names = list(model_dict['outputs']['actual'].keys())
    num_vars = len(out_var_names)
    num_pts = len(ukf_input_dict['analyticSettings']['model']['outputs']['actual'][out_var_names[0]])

    tunableParams = model_dict['analyticSettings']['tunableParams']
    n_inp_vars = 0
    for key, value in tunableParams.items():
        n_inp_vars += len(value)
    dim_x = n_inp_vars
    dim_y = num_pts * num_vars

    dt = 1
    alpha = ukf_settings['alpha']
    beta = ukf_settings['beta']
    kappa = ukf_settings['kappa']
    ukf_params = [alpha[0], beta[0], kappa[0]]
    P = ukf_settings['P']
    Q = ukf_settings['Q']
    R = ukf_settings['R']
    max_iter = ukf_settings['max_iter'][0]

    ukf = UnscentedKFGRPC(dim_x=dim_x, dim_y=dim_y, dt=dt, fx=fx, grpc_hx=grpc_hx, grpc_stub=grpc_stub,
                          ukf_params=ukf_params)

    model_analytic_settings = ukf_input_dict['analyticSettings']['model']['analyticSettings']
    tunable_params = list(model_analytic_settings['tunableParams'].keys())

    x_list = list()
    x_name_len_list = list()

    for params in tunable_params:
        this_var_list = model_analytic_settings['tunableParams'][params]
        x_name_len_list.append((params, len(this_var_list)))
        for val in this_var_list:
            x_list.append(val)

    ukf.x_name_len_list = x_name_len_list
    ukf.x = np.array(x_list)
    ukf.P = np.diag(P)
    if len(R) == 1:
        ukf.R = R[0]
    else:
        ukf.R = np.diag(R)
    ukf.Q = np.diag(Q)
    ukf.max_iter = max_iter
    return ukf
