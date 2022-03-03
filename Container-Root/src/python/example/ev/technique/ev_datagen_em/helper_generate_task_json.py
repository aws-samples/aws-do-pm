######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import json

# Load template
task_template = 'task_template.json'
with open(task_template, 'r') as fp:
    task_json = json.load(fp)

# pm to update these values
task_json['task_id'] = 'trial1'
task_json['analyticSettings']['rel_dest_path'] = 'data/trial1'

# Resulting task json
print(json.dumps(task_json, indent=2))
# conda activate pm_py39
# python norm_route_generator.py --task-json-path <root relative location of task file>