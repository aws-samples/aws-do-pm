######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import argparse
import os
import model

if __name__ == '__main__':

    #import debugpy; debugpy.listen(('0.0.0.0',5677)); debugpy.wait_for_client(); breakpoint()
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to task configuration json")
    args = parser.parse_args()

    if args.config is None:
        print("Please specify path to the model task configuration using the --config option")
    elif not os.path.exists(args.config):
        print("Path %s not found"%args.config)
    else:
        model.register_model(args.config)

    # Return, framework creates new data or error node in graph
