######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import argparse
import service 

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='Service configuration template with provided values')
    args = parser.parse_args()
    config = args.config
    if (config == ''): 
        print("Please specify service task config using the --config argument")
    else:
        service.destroy_service(config)
    