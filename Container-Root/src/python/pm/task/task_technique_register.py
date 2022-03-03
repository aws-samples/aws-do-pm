######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import argparse
import technique
import lib.db.graph.dba as dba
import lib.db.graph.data as graphdata
import pm.technique.technique as technique
import json
from datetime import datetime

if __name__ == '__main__':

    #import debugpy; debugpy.listen(('0.0.0.0',5678)); debugpy.wait_for_client(); breakpoint()

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='Technique configuration, template with provided values')
    args = parser.parse_args()
    if (args.config is None):
        print("Please specify config path using the --config argument")
    else:
        techique_config=""
        with open(args.config, 'r') as fp:
            task_properties = json.load(fp)
            analytic_settings = task_properties["analyticSettings"]
            technique_config = analytic_settings["config"]
            with open(technique_config, 'r') as tc:
                technique_properties = json.load(tc)
                technique_id = task_properties['output_artifacts']['technique'][0]
                technique_properties['technique_id'] = technique_id
                technique_properties['created_dt'] = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
            tc.close()
        fp.close()
        if technique_properties is not None:
            technique_id = technique.register_technique_json(technique_properties)
            #print('technique/%s'%technique_id)
        else:
            print('Error')
