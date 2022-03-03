######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

def create_ukf_input_dict(model_dict, max_iter=20):
    # Find Length of the stacked input of all the list
    tunableParams = model_dict['analyticSettings']['tunableParams']
    n_inp_vars = 0
    for key, value in tunableParams.items():
        n_inp_vars += len(value)

    input_dict = {
        "task": "update",
        "technique": "ukf",
        "dataLocation": "",
        "infraSettings": {},
        "analyticSettings": {
            "model":model_dict,
            "ukf":{
                'alpha': [1],
                'beta': [2],
                'kappa': [0],
                'P': n_inp_vars * [0.0001], #[1, 0.0001],
                'Q': n_inp_vars * [0.0001], #[1, 0.0001],
                'R': [0.0001],
                'max_iter': [max_iter]
            }
        },
        "inputs": {
        },
        "outputs": {
        },
        "savedState": {
        }
    }
    return input_dict

