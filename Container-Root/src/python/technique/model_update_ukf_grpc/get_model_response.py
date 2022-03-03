######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

from grpc_compiled import model_interface_pb2, model_interface_pb2_grpc
from lib.util.encode_decode_json import utf_encode_json, utf_decode_json

# Perform model prediction and return the prediction in a dictionary
def get_model_response(model_dict, stub):
    model_dict_enc = utf_encode_json(model_dict)
    query = model_interface_pb2.inRequest(inp_dict_bytes=model_dict_enc)
    response = stub.EvaluateModel(query)
    response_dict = utf_decode_json(response.response_bytes)

    return response_dict