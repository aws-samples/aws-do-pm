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

def list_data(verbose=True):
    data = graphdata.get_vertices('data',graph)
    data_id_list = []
    data_map = {}
    if data is not None:
        c = data.all()
        while (not c.empty()):
            d = c.next()
            data_id = d['_key']
            if 'metadata' in d:
                metadata = d['metadata']
                if 'filename' in metadata:
                    data_filename=metadata['filename']
                else:
                    data_filename=''
                if 'description' in metadata:
                    data_description=metadata['description']
                else:
                    data_description=''
            if 'created_dt' in d:
                data_created_dt = d['created_dt']
            else:
                data_created_dt = ''
            map_dict = {
                'filename': data_filename,
                'description': data_description,
                'created_dt': data_created_dt
            }
            data_map[data_id] = map_dict
            if verbose:
                print('%s %s %s %s'%(data_id,data_created_dt,data_filename,data_description))
            data_id_list.append(data_id)
    return data_id_list, data_map    

def describe_data(data_id):
    vertex = graphdata.get_vertex('data',data_id,graph)
    print(json.dumps(vertex['metadata'],indent=2))

def get_parent_task_id(data_id,verbose=True):
    parent_ids = graphdata.get_vertex_parent_ids('data',data_id,graph,verbose=True)
    # In Arangodb syntax _id=data/KJHLWERWESD and _key=KJHLWERWESD
    task_id=''
    for id in parent_ids:
        if id.startswith('task/'):
            task_id=id.replace('task/','')
            break
    if verbose:
        print("task_id=%s"%task_id)
    return task_id

def delete_data(data_id):
    raise Exception('Cannot delete data %s. Method not implemented'%str(data_id))

def register_data(config):

    task_json_path_full = '%s' % (config)
    task_dict = file_util.read_json(task_json_path_full)

    #print(task_dict)
    
    # 0) Configure environment
    container_env = os.environ.copy()
    aws_opts = os.getenv('AWS_OPTS', default='--no-cli-pager')
    pm_root_path = os.getenv('PM_ROOT_PATH', default='wd')
    aws_id = file_util.read_line('%s/.aws_id'%pm_root_path)
    container_env['AWS_ACCESS_KEY_ID']=aws_id
    aws_cr = file_util.read_line('%s/.aws_cr'%pm_root_path)
    container_env['AWS_SECRET_ACCESS_KEY'] = aws_cr

    # 1) Upload dataset to S3
    pm_s3_bucket = task_dict['analyticSettings']['pm_s3_bucket']
    rel_dest_path = task_dict['analyticSettings']['rel_dest_path']
    local_path = task_dict['analyticSettings']['local_path']
    cmd=['aws %s s3 sync %s s3://%s/%s'%(aws_opts,local_path,pm_s3_bucket,rel_dest_path)]
    completed_process = subprocess.run(cmd,shell=True,capture_output=True,check=True,env=container_env)
    print(completed_process.stdout.decode())
    if completed_process.returncode != 0:
        print("STDERRR:")
        print(completed_process.stderr.decode())
    
    # 2) Download dataset locally
    dest_path = '%s/%s'%(pm_root_path,rel_dest_path)
    os.makedirs(dest_path,exist_ok=True)
    cmd=['aws %s s3 sync s3://%s/%s %s'%(aws_opts,pm_s3_bucket,rel_dest_path,dest_path)]
    completed_process = subprocess.run(cmd,shell=True,capture_output=True,check=True, env=container_env)
    print(completed_process.stdout.decode())
    print(completed_process.stderr.decode())

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
    filename = task_dict['analyticSettings']['filename']
    metadata_path='%s/%s/metadata.json'%(pm_root_path,rel_dest_path)
    metadata={}
    if os.path.exists(metadata_path):
        # If metadata already exists, merge it
        metadata = file_util.read_json(metadata_path)
    metadata['node_name']='data'
    metadata['created_dt']=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    if 'metadata' not in metadata:
        # Create a dummy place holder for metadata key
        metadata['metadata'] = {}
    metadata_updated = metadata['metadata']
    if metadata_updated is None:
        metadata_updated={}
    if isinstance(metadata_updated,list):
        metadata_updated={'list': metadata_updated}
    metadata_updated['rel_dest_path']=rel_dest_path
    metadata_updated['filename'] = filename
    metadata_updated['description']=data_description
    metadata_updated['catalog']=relative_catalog
    # TODO: Make it generic (hardcoding the filename for now)
    metadata_updated['filename'] = 'input_output.json'
    metadata['metadata'] = metadata_updated
    file_util.write_json(metadata_path,metadata)

    # 4) Sync metadata back to S3
    cmd=['aws %s s3 sync %s s3://%s/%s'%(aws_opts,dest_path,pm_s3_bucket,rel_dest_path)]
    completed_process = subprocess.run(cmd,shell=True,capture_output=True,check=True, env=container_env)
    print(completed_process.stdout.decode())
    print(completed_process.stderr.decode()) 

    return True



if __name__ == '__main__':

    #import debugpy; debugpy.listen(('0.0.0.0',5677)); debugpy.wait_for_client(); breakpoint()
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', help='Data action: ls | describe | generate | register | delete | parents')
    parser.add_argument('--id', help='Data unique identifier if needed by action')
    parser.add_argument('--config', help='Path to data related task configuration json')    
    args = parser.parse_args()

    action = args.action
    if (action == 'ls'):
        list_data()
    elif (action == 'describe'):
        if (args.id is None):
            print("Please specify data id using the --id argument")
        else:
            describe_data(args.id)
    elif (action == 'delete'):
        if (args.id is None):
            print("Please specify data id using the --id argument")
        else:
            delete_data(args.id)
    elif (action == 'parents'):
        if (args.id is None):
            print("Please specify data id using the --id argument")
        else:
            get_parent_task_id(args.id)
    else:
        print("Action %s not recognized"%action)

 
