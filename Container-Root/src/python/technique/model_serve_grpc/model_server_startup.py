######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import argparse
import os
import json
import time
import grpc
import sys
from pathlib import Path
import model_server

sys.path.append("/app/grpc_compiled")
from grpc_compiled import model_interface_pb2, model_interface_pb2_grpc

def check_health():
    channel = grpc.insecure_channel('localhost:13000')
    stub = model_interface_pb2_grpc.ModelServiceStub(channel)
    try:
        #import pdb; pdb.set_trace()
        print("Checking health ...")
        empty = model_interface_pb2.google_dot_protobuf_dot_empty__pb2.Empty()
        loc_reply = stub.HealthCheck(empty)
        print("Returned health check ...")
        print(loc_reply)
        print(loc_reply.status)
        if (loc_reply.status == "SERVING"):
            return True
        else:
            return False
    except Exception as e:
        print("Exception")
        print(e)
        #traceback.print_exc(e)
        return False

if __name__ == '__main__':
    #import debugpy; debugpy.listen(('0.0.0.0',5676)); debugpy.wait_for_client(); breakpoint()

    print("Executing model server startup ...")
    sys.stdout.flush()
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='Path to model server configuration json')
    args = parser.parse_args()
    config = args.config

    server_config_json={}
    internal_port = 13000
    processor = "cpu"
    pm_root_path=os.getenv("PM_ROOT_PATH",default="wd")
    startup_timeout_sec = 60
    #import pdb; pdb.set_trace()
    if config != "":
        if os.path.exists(config):
            print("Using settings from specified config file %s"%config)
            with open(config, 'r') as fp:
                server_config_json = json.load(fp)
            analytic_settings = server_config_json["analyticSettings"]
            group_id = analytic_settings["group_id"]
            rel_model_path = analytic_settings["rel_model_path"]
            internal_port = analytic_settings["internal_port"]
            processor = analytic_settings["processor"]
            startup_timeout_sec = analytic_settings["startup_timeout_sec"]
        else:
            print("Specified config file %s not found, using default settings."%config)
    else:
        print("No server config specified, using default settings.")

    # Get model path from metadata
    with open('%s/%s/model.json'%(pm_root_path,rel_model_path), 'r') as fp:
        model_dict = json.load(fp)
    model_loc = model_dict["analyticSettings"]["model_filepath_full"]
    model_loc_full = '%s'%(model_loc)
    # Parse config and set environment required by server
    server_env = os.environ.copy()
    server_env["MODEL_LOC"] = model_loc_full
    server_env["PORT_INTERNAL"] = str(internal_port)
    server_env["PROCESSOR"] = processor
    server_env["STARTUP_TIMEOUT_SEC"] = str(startup_timeout_sec)
    os.environ['MODEL_LOC'] = model_loc_full
    os.environ['PORT_INTERNAL'] = str(internal_port)
    os.environ['PROCESSOR'] = processor
    os.environ['STARTUP_TIMEOUT_SEC'] = str(startup_timeout_sec)

    # Write service metadata
    service_id = server_config_json['output_artifacts']['service'][0]
    metadata_folder = '%s/service/%s'%(pm_root_path,service_id)
    metadata_filepath = '%s/metadata.json'%(metadata_folder)
    sys.stdout.flush()
    metadata = {'metadata':{}}
    # Pack the model into the metadata
    metadata["metadata"]["model"] = model_dict
    metadata["metadata"]["group_id"] = group_id
    metadata["metadata"]["model_id"] = server_config_json["input_artifacts"]["model"][0]
    metadata["metadata"]["updated_dt"]=time.strftime("%Y%m%d-%H%M%S")
    metadata["metadata"]["port_internal"]=internal_port
    metadata["metadata"]["model_loc"] = model_loc
    metadata["metadata"]["processor"] = processor
    metadata["metadata"]["startup_timeout_sec"] = startup_timeout_sec
    metadata["metadata"]["name"] = 'service-%s'%service_id

    out_file_path = Path(metadata_filepath)
    out_file_path.parent.mkdir(exist_ok=True, parents=True)
    print("Saving service metadata to %s"%metadata_filepath)
    with open(metadata_filepath, 'w') as fp:
        json.dump(metadata,fp)
        fp.flush()
        os.fsync(fp.fileno())
    fp.close()

    # Sync parent directory
    fd = os.open(metadata_folder, os.O_RDONLY)
    os.fsync(fd)
    os.close(fd)


    # Start service
    print('Starting service on port %s ...'%str(internal_port))
    sys.stdout.flush()
    model_server.serve()

    # If serve() returns it means the service is stopped
    print('Model service stopped')
    sys.stdout.flush()
    