######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import os
import argparse
import lib.db.graph.dba as dba
import lib.db.graph.data as graphdata
import json
import glob
import datetime
import subprocess
import lib.util.file_util as file_util

graph = dba.get_graph()

def list_model(verbose=True):
    models = graphdata.get_vertices('model',graph)
    model_id_list = []
    model_map = {}
    if models is not None:
        c = models.all()
        while (not c.empty()):
            m = c.next()
            model_id = m['_key']
            if 'metadata' in m:
                metadata = m['metadata']
                if 'filename' in metadata:
                    model_filename=metadata['filename']
                else:
                    model_filename=''
                if 'description' in metadata:
                    model_description=metadata['description']
                else:
                    model_description=''
            if 'created_dt' in m:
                model_created_dt = m['created_dt']
            else:
                model_created_dt = ''
            map_dict = {
                'filename': model_filename,
                'description': model_description,
                'created_dt': model_created_dt
            }
            model_map[model_id] = map_dict
            if verbose:
                print('%s %s %s %s'%(model_id,model_created_dt,model_filename,model_description))
            model_id_list.append(model_id)
    return model_id_list, model_map  

def describe_model(model_id):
    vertex = graphdata.get_vertex('model',model_id,graph)
    print(json.dumps(vertex['metadata'],indent=2))

def delete_model(model_id):
    raise Exception('Cannot delete model %s. Method not implemented'%str(model_id))

def register_model(config):

    task_dict = file_util.read_json(config)

    #print(task_dict)
    
    # 0) Configure environment
    container_env = os.environ.copy()
    aws_opts = os.getenv('AWS_OPTS', default='--no-cli-pager')
    pm_root_path = os.getenv('PM_ROOT_PATH', default='wd')
    aws_id = file_util.read_line('%s/.aws_id'%pm_root_path)
    container_env['AWS_ACCESS_KEY_ID']=aws_id
    aws_cr = file_util.read_line('%s/.aws_cr'%pm_root_path)
    container_env['AWS_SECRET_ACCESS_KEY'] = aws_cr

    # 1) Upload model to S3
    pm_s3_bucket = task_dict['analyticSettings']['pm_s3_bucket']
    rel_dest_path = task_dict['analyticSettings']['rel_dest_path']
    cmd=['aws',aws_opts,'s3','sync','/register','s3://%s/%s'%(pm_s3_bucket,rel_dest_path)]
    completed_process = subprocess.run(cmd,shell=False,capture_output=True,check=True,env=container_env)
    print(completed_process.stdout.decode())
    #print(completed_process.stderr.decode())
    
    # 2) Download model locally
    dest_path = '%s/%s'%(pm_root_path,rel_dest_path)
    os.makedirs(dest_path,exist_ok=True)
    cmd=['aws',aws_opts,'s3','sync','s3://%s/%s'%(pm_s3_bucket,rel_dest_path),dest_path]
    completed_process = subprocess.run(cmd,shell=False,capture_output=True,check=True, env=container_env)
    print(completed_process.stdout.decode())
    #print(completed_process.stderr.decode())

    # 3) Create and save metadata locally
    catalog = glob.glob('%s/**'%dest_path,recursive=True)
    relative_catalog = []
    base_path = dest_path
    if not base_path.endswith('/'):
        base_path = '%s/'%base_path
    for f in catalog:
        if os.path.isfile(f):
            relative_catalog.append(f.replace(base_path,''))
    data_description = task_dict['analyticSettings']['description']
    metadata_path='%s/%s/metadata.json'%(pm_root_path,rel_dest_path)
    metadata={}
    if os.path.exists(metadata_path):
        metadata = file_util.read_json(metadata_path)
    metadata['node_name']='model'
    metadata['created_dt']=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    metadata['metadata']['rel_dest_path']=rel_dest_path
    metadata['metadata']['description']=data_description
    metadata['metadata']['catalog']=relative_catalog
    file_util.write_json(metadata_path,metadata)

    # 4) Sync metadata back to S3
    cmd=['aws',aws_opts,'s3','sync',dest_path,'s3://%s/%s'%(pm_s3_bucket,rel_dest_path)]
    completed_process = subprocess.run(cmd,shell=False,capture_output=True,check=True, env=container_env)
    print(completed_process.stdout.decode())
    #print(completed_process.stderr.decode()) 

    return True

if __name__ == '__main__':

    #import debugpy; debugpy.listen(('0.0.0.0',5677)); debugpy.wait_for_client(); breakpoint()
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', help='Data action: ls | describe | generate | register | delete ')
    parser.add_argument('--id', help='Data unique identifier if needed by action')
    parser.add_argument('--config', help='Path to data related task configuration json')    
    args = parser.parse_args()

    action = args.action
    if action is None:
        print("Please specify action using the --action argument")
    else:
        if (action == 'ls'):
            list_model(verbose=True)
        elif (action == 'describe'):
            if (args.id is None):
                print("Please specify data id using the --id argument")
            else:
                describe_model(args.id)
        elif (action == 'delete'):
            if (args.id is None):
                print("Please specify data id using the --id argument")
            else:
                delete_model(args.id)
        elif (action == 'register'):
            if (args.config is None):
                print("Please specify model registration task config path using the --config argument")
            else:
                register_model(args.config)
        else:
            print("Action %s not recognized"%action)

 
