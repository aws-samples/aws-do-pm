######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

from concurrent import futures
import sys
import os
import grpc
import time

sys.path.append("/app/grpc_compiled")

from grpc_compiled import model_interface_pb2, model_interface_pb2_grpc
from lib.util.encode_decode_json import utf_encode_json, utf_decode_json
from torchhandler_atomic import initialize, run
from grpc_health.v1 import health_pb2, health_pb2_grpc
from grpc_health.v1.health import HealthServicer

class ModelService(model_interface_pb2_grpc.ModelServiceServicer):
    def __init__(self, health):
        self.health=health
        print('Initializing Health Object in Server with Non Serving Status')
        self.health.set(
            "modelservice",
            health_pb2.HealthCheckResponse.ServingStatus.Value("NOT_SERVING"),
        )
        server_start_time = time.time()
        self.loaded = False
        # All one time initialization entities go here
        model_loc = os.getenv('MODEL_LOC')
        print('Loading Model: %s' % (model_loc))

        # Determine processor setting
        processor = os.getenv('PROCESSOR', default='cpu')
        print('Running model on %s' % (processor))
        gpu_mode = True
        if processor == 'cpu':
            gpu_mode = False

        # Initialization Code
        init_dict = initialize(model_loc=model_loc, gpu_mode=gpu_mode)

        print('Loaded Model, Setting modelservice to Serving status')
        self.health.set(
            "modelservice",
            health_pb2.HealthCheckResponse.ServingStatus.Value("SERVING"),
        )
        # print('Loaded')
        self.loaded = True
        self.init_dict = init_dict

    def HealthCheck(self, request, context):
        if(self.loaded):
            return model_interface_pb2.HCReply(status="SERVING")
        else:
            return model_interface_pb2.HCReply(status="NOT_SERVING")

    def EvaluateModel(self, request, context):
        print('Evaluating model  ...')
        inp_dict_bytes = request.inp_dict_bytes
        inp_dict = utf_decode_json(inp_dict_bytes)

        # analyticSettings_bytes = request.analytic_settings

        # Decode the bytes back into json
        # analyticSettings = utf_decode_json(analyticSettings_bytes)
        out_dict = run(inp_dict=inp_dict,
                       **self.init_dict)

        # Compose return Object
        ret_dict = {
            'prediction': out_dict
        }

        ret_dict_encoded = utf_encode_json(ret_dict)
        return model_interface_pb2.outCalc(response_bytes=ret_dict_encoded)


def serve():
    SERVER_PORT = os.getenv('PORT_INTERNAL', 13000)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    # As with any other Servicer implementations, register it
    health = HealthServicer()
    modelservice = ModelService(health)

    model_interface_pb2_grpc.add_ModelServiceServicer_to_server(modelservice, server)
    health_pb2_grpc.add_HealthServicer_to_server(health, server)
    # server.add_insecure_port('[::]:13000')
    print('Starting model service on port %s' % SERVER_PORT)
    sys.stdout.flush()
    server.add_insecure_port('[::]:%s' % SERVER_PORT)
    server.start()
    print("Server started. Awaiting jobs...")
    sys.stdout.flush()
    sys.stderr.flush()
    try:
        while True:  # since server.start() will not block, a sleep-loop is added to keep alive
            time.sleep(60)
            print("Server is running and awaiting jobs ...")
            sys.stdout.flush()
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    print('Model Server: Triggering server start')
    serve()
