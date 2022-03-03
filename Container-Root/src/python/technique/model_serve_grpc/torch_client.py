######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import sys
import grpc
import argparse

sys.path.append("/app/grpc_compiled")
import numpy as np
from grpc_compiled import model_interface_pb2, model_interface_pb2_grpc
from lib.util.encode_decode_json import utf_encode_json
from tqdm import tqdm
from lib.grpc.retry_interceptor import RetryOnRpcErrorClientInterceptor, ExponentialBackoff


def run(hostname,port):
    address='%s:%s'%(hostname,port)

    interceptors = (
        RetryOnRpcErrorClientInterceptor(
            max_attempts=5,
            sleeping_policy=ExponentialBackoff(init_backoff_ms=1000, max_backoff_ms=30000, multiplier=2),
            status_for_retry=(grpc.StatusCode.UNAVAILABLE,),
        ),
    )
    stub = model_interface_pb2_grpc.ModelServiceStub(
        grpc.intercept_channel(grpc.insecure_channel(address), *interceptors)
    )
    loc_inp_dict = {}

    loc_analyticSettings = {}
    loc_analyticSettings['modelParams'] = {
        "input_var_order": ["x_1", "x_2", "x_3"],
        "output_var_order": ["y_1"],
        # "bias_weight_array": np.ones((5,)).tolist(),
        "bias_weight_map": {
            "final": {
                "weights": [1, 2, 3, 4],
                "bias": [0]
            }
        }
    }
    loc_analyticSettings['tunableParams'] = {
        "bias_weight_array": np.random.random(5, ).tolist()
    }

    # Set the Inputs
    n_rows = 50
    inputs = {}
    for idx, cur_var in enumerate(loc_analyticSettings['modelParams']['input_var_order']):
        inputs[cur_var] = np.random.random(n_rows).tolist()

    loc_inp_dict['analyticSettings'] = loc_analyticSettings
    loc_inp_dict['inputs'] = inputs

    loc_inp_dict_encoded = utf_encode_json(loc_inp_dict)

    query = model_interface_pb2.inRequest(inp_dict_bytes=loc_inp_dict_encoded)
    nRuns = 1000
    for _ in tqdm(range(nRuns)):
        response = stub.EvaluateModel(query)

    # Convert to dataframe and print the contents
    print(response)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--hostname', help='Name of the model server to connect to', default='localhost')
    parser.add_argument('--port', help='port of the model server to connect to', default='13000')
    args = parser.parse_args()
    run(args.hostname,args.port)
