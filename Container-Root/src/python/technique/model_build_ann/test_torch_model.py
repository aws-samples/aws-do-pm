######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import numpy as np
from torchhandler_atomic import initialize, run, cleanup

if __name__ == "__main__":
    import os

    run_id = os.getenv('PM_ID')
    model_loc = '/wd/model/%s/mlp_train.pth'%(run_id)
    print('Initializing w/:%s' % (model_loc))
    # Determine processor setting
    processor = os.getenv('PROCESSOR', default='cpu')
    print('Running model on %s' % (processor))
    gpu_mode = True
    if processor == 'cpu':
        gpu_mode = False
    init_dict = initialize(model_loc=model_loc, gpu_mode=gpu_mode)

    inp_dict = {}

    loc_analyticSettings = {}
    loc_analyticSettings['modelParams'] = {
        "input_var_order": ["x_1", "x_2", "x_3"],
        "output_var_order": ["y_1"],
        # "bias_weight_array": list(np.ones((5,))),
        "bias_weight_map": {
            "final": {
                "weights": [1, 2, 3, 4],
                "bias": [0]
            }
        }
    }
    loc_analyticSettings['tunableParams'] = {
        "bias_weight_array": list(np.random.random(5, ))
    }

    # Set the Inputs
    n_rows = 10
    inputs = {}
    for idx, cur_var in enumerate(loc_analyticSettings['modelParams']['input_var_order']):
        inputs[cur_var] = np.random.random(n_rows).tolist()

    inp_dict['analyticSettings'] = loc_analyticSettings
    inp_dict['inputs'] = inputs

    print('Simulating')
    ret_dict = run(inp_dict=inp_dict,
                   **init_dict)

    print(ret_dict)

    print('Clean Up')
    cleanup(**init_dict)
