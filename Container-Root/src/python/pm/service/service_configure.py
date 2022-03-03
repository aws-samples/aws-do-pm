######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import argparse
import os
import json
import time
import sys
from pathlib import Path

if __name__ == '__main__':
    # import debugpy; debugpy.listen(('0.0.0.0',5676)); debugpy.wait_for_client(); breakpoint()

    print("Executing plug model into service ...")
    sys.stdout.flush()
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='Path to service update configuration json')
    args = parser.parse_args()
    config = args.config
    pm_root_path = os.getenv("PM_ROOT_PATH", default="wd")

    if os.path.exists(config):
        print("Using settings from specified config file %s" % config)
        with open(config, 'r') as fp:
            server_update_json = json.load(fp)
        analytic_settings = server_update_json["analyticSettings"]
        rel_service_path = analytic_settings["rel_service_path"]
        rel_model_path = analytic_settings["rel_model_path"]

        # Get model path from metadata
        with open('%s/%s/model.json' % (pm_root_path, rel_model_path), 'r') as fp:
            model_dict = json.load(fp)

        # Get model path from metadata
        metadata_filepath = '%s/%s/metadata.json' % (pm_root_path, rel_service_path)
        with open(metadata_filepath, 'r') as fp:
            service_metadata_dict = json.load(fp)

        # Plug in the new model dict into it
        # Retain the rest as it is
        service_metadata_dict['metadata']['model'] = model_dict
        service_metadata_dict["metadata"]["updated_dt"] = time.strftime("%Y%m%d-%H%M%S")

        # Write back the contents into the same service's metadata
        print("Saving updated service metadata to %s" % metadata_filepath)
        with open(metadata_filepath, 'w') as fp:
            json.dump(service_metadata_dict, fp)
    else:
        print("Specified config file %s not found, skipping." % config)

