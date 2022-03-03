######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import argparse
from pickle import APPEND
import lib.db.graph.dba as dba
import lib.db.graph.data as graphdata
import lib.util.list_util as list_util
import lib.util.dict_util as dict_util
import json
import os
from pathlib import Path

graph = dba.get_graph()

def list_techniques(tags, verbose=True):
    technique = graphdata.get_vertices('technique',graph)
    technique_id_list = []
    technique_tag_list=[[]]
    c = technique.all()
    while (not c.empty()):
        t = c.next()
        technique_id = t['technique_id']
        technique_name = t['technique_name']
        technique_tags=t['technique_tags']
        technique_description=t['technique_description']
        check = all(item in technique_tags for item in tags)
        if check:
            if verbose:
                print('%s %s %s %s'%(technique_id,technique_name,technique_tags,technique_description))
            technique_id_list.append(technique_id)
            technique_tag_list.append(technique_tags)
    return technique_id_list,technique_tag_list

def describe_technique(technique_id):
    technique = graphdata.get_vertex('technique', technique_id, graph)
    print(json.dumps(technique,indent=2))
    return technique

def export_task_template(technique_id, verbose=True):
    technique = graphdata.get_vertex('technique', technique_id, graph)
    task_template = technique['task_template']
    if verbose:
        print(json.dumps(task_template, indent=2))
    return task_template

def search_export_task_template(tags):
    technique_id_list,technique_tag_list = list_techniques(tags,verbose=False)
    tag_str = ' '.join(tags)
    if len(technique_id_list) < 1:
        output = 'Sorry, do not know how to go %s'%tag_str
    elif len(technique_id_list) > 1:
        full_list = list_util.flatten_list_of_lists(technique_tag_list)
        union = list_util.unique_list(full_list)
        diff = list_util.diff_lists(union,tags)
        output = 'Please qualify further: %s'%diff
    else:
        task_template = export_task_template(technique_id_list[0], verbose=False)
        task_template_updated = dict_util.replace_keywords(task_template)
        output=json.dumps(task_template_updated, indent=2, ensure_ascii=True)
    print(output)

def delete_technique(technique_name):
    techniques = graph.vertex_collection('technique')
    techniques.delete(technique_name)

def get_task_template_filepath(technique_name):
    technique = describe_technique(technique_name)
    task_template_filepath = technique["task_template_filepath"]
    return task_template_filepath

def get_task_template_file(technique_name):
    task_template_filepath = get_task_template_filepath(technique_name)
    template={}
    with open(task_template_filepath, 'r') as fp:
        template = json.load(fp)
    fp.close()
    return template

def get_task_executor_filepath(technique_name):
    technique = describe_technique(technique_name)
    task_executor_filepath = technique["task_executor_filepath"]
    return task_executor_filepath

def register_technique(technique_config):
    technique_properties={}
    with open(technique_config, 'r') as fp:
        technique_properties = json.load(fp)
    fp.close()
    technique_id = register_technique_json(technique_properties)
    return technique_id

def register_technique_json(technique_properties):
    # Construct technique folder: ${PM_ROOT_PATH}/technique/<technique_id>
    cur_technique_id = technique_properties['technique_id']
    pm_root_path = os.getenv('PM_ROOT_PATH', default='wd')
    technique_output_json_filepath_full = '%s/technique/%s/metadata.json' % (pm_root_path, cur_technique_id)    
    out_file_path = Path(technique_output_json_filepath_full)
    out_file_path.parent.mkdir(exist_ok=True, parents=True)
    # Write technique json to folder
    with open(technique_output_json_filepath_full, 'w') as fp:
        json.dump(technique_properties,fp)
    return cur_technique_id

if __name__ == '__main__':

    #import debugpy; debugpy.listen(('0.0.0.0',5678)); debugpy.wait_for_client(); breakpoint()

    parser = argparse.ArgumentParser()
    parser.add_argument('--action', help='Technique action: ls | describe | template | search | register | delete', required=True)
    parser.add_argument('--tags', help='Technique selection tags, a space separated string, can be combined with --action ls or --action search', nargs='+', default=[], required=False)
    parser.add_argument('--technique_id', help='Technique id', required=False)
    parser.add_argument('--config', help='Technique configuration, template with provided values', required=False)
    args = parser.parse_args()
    action = args.action
    if (action == 'ls'): 
        list_techniques(args.tags)
    elif (action == 'search'):
        search_export_task_template(args.tags)
    elif (action == 'describe'):
        if (args.technique_id is None):
            print("Please specify technique id using the --technique_id argument")
        else:
            describe_technique(args.technique_id)
    elif (action == 'template'):
        if (args.technique_id is None):
            print("Please specify technique id using the --technique_id argument")
        else:
            export_task_template(args.technique_id)
    elif (action == 'delete'):
        if (args.technique is None):
            print("Please specify technique id using the --technique_id argument")
        else:
            delete_technique(args.technique_id)
    elif (action == 'register'):
        if (args.config is None):
            print("Please specify config path using the --config argument")
        else:
            register_technique(args.config)
    else:
        print('Action %s not recognized'%action)
    
