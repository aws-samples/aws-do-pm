######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import argparse
import lib.uid_generator as uid_generator
import lib.db.graph.dba as dba
import lib.db.graph.data as graphdata
import subprocess
import json
import os

graph = dba.get_graph()
db = dba.get_db()

def list_deleted_services(verbose=False):
    aql_str = "FOR svc IN service" \
              "  FOR lnk1 IN link" \
              "    FILTER svc.`_id` == lnk1.`_from`" \
              "    FOR tsk in task" \
              "      FILTER tsk.`_id` == lnk1.`_to`" \
              "      FILTER tsk.`node_name` == 'destroy'" \
              "      FOR lnk2 in link" \
              "        FILTER lnk2.`_from` == tsk.`_id`" \
              "        FOR tsh in trash" \
              "          FILTER tsh.`_id`== lnk2.`_to`" \
              "RETURN {svc,lnk1,tsk,lnk2,tsh}"
    cursor = db.aql.execute(aql_str,batch_size=1,count=True)
    if verbose:
        print('There are %s deleted services'%cursor.count())
    deleted_service_ids=[]
    while cursor.has_more():
        s = cursor.next()
        s_id = s['svc']['_key']
        deleted_service_ids.append(s_id)
        
    if verbose:
        print(deleted_service_ids)
        
    return deleted_service_ids

def list_services(verbose=True):
    service = graphdata.get_vertices('service',graph)
    service_id_list = []
    service_map = {}
    if not service is None:
        deleted_service_ids = list_deleted_services(verbose=False)
        c = service.all()
        while not c.empty():
            s = c.next()
            service_id = s['_key']
            if not service_id in deleted_service_ids:
                if 'metadata' in s:
                    metadata = s['metadata']
                    if 'model_id' in metadata:
                        model_id = metadata['model_id']
                    else:
                        model_id = ''
                    if 'name' in metadata:
                        name = metadata['name']
                    else:
                        name = ''
                    if 'port_internal' in metadata:
                        port_internal = metadata['port_internal']
                    else:
                        port_internal = ''
                    if 'updated_dt' in metadata:
                        updated_dt = metadata['updated_dt']
                    else:
                        updated_dt = ''
                    if 'group_id' in metadata:
                        group_id = metadata['group_id']
                    else:
                        group_id = ''
                if 'created_dt' in s:
                    created_dt = s['created_dt']
                else:
                    created_dt = ''
                map_dict = {
                    'created_dt': created_dt,
                    'updated_dt': updated_dt,
                    'model_id': model_id,
                    'group_id': group_id,
                    'name': name,
                    'port_internal': port_internal,
                }
                service_map[service_id] = map_dict
                if verbose:
                    print('%s %s %s %s %s %s %s'%(service_id, group_id, created_dt, updated_dt, model_id, name, port_internal))
                service_id_list.append(service_id)
        
    return service_id_list, service_map

#def list_services():
#    pm_root_dir = os.getenv('PM_ROOT_DIR',default='wd')
#    cmd=['ls','-alh','%s/service/'%pm_root_dir]
#    completed_process = subprocess.run(cmd,shell=True,capture_output=True)
#    print(completed_process.stdout)

def describe_service(service_id):
    service = graphdata.get_vertex('service',service_id,graph)
    print(json.dumps(service['metadata'], indent=2))

def check_service_status(service_id):
    service = graphdata.get_vertex('service',service_id,graph)
    name=service["metadata"]["name"]
    port_internal=service["metadata"]["port_internal"]
    cmd=["grpcurl","--plaintext","-d","{\"service\":\"modelservice\"}",
         "-import-path","/src/python/technique/model_serve_grpc","-proto", "health.proto", 
         "-proto","model_interface.proto",'%s:%s'%(name,port_internal),
         "grpc.health.v1.Health/Check"]
    print(cmd)
    completed_process = subprocess.run(cmd,shell=False,capture_output=True)
    print(completed_process.stdout.decode())
    print(completed_process.stderr.decode())

def destroy_service(config):
    
    with open(config,'r') as fp:
        task_config = json.load(fp)

    service_id = task_config['input_artifacts']['service'][0]
    trash_id = task_config['output_artifacts']['trash'][0]
    
    service = graphdata.get_vertex('service',service_id,graph)
    name = service['metadata']['name']
    to=os.getenv('TO', default='docker')
    cmd=[]
    if to == 'kubernetes':
        namespace = os.getenv('NAMESPACE', default='aws-do-pm')
        try:
            service_json_completed_cmd = subprocess.run(['kubectl','-n',namespace,'get','service',name,'-o','json'],capture_output=True)
            jq_completed_cmd = subprocess.run(['jq','-r','.spec.selector.run'], input=service_json_completed_cmd.stdout, capture_output=True)
            pod_name = jq_completed_cmd.stdout.decode()
            pod_name = pod_name.strip()
            kubectl_completed_delete_cmd = subprocess.run(['kubectl','-n',namespace,'delete','pod',pod_name,'--wait=false'],capture_output=True)
            print(kubectl_completed_delete_cmd.stdout.decode())
        except subprocess.CalledProcessError as cpe:
            print(cpe.stderr)
            raise cpe
        cmd.extend(['kubectl','-n',namespace,'delete','service',name,'--wait=false'])
    else:
        cmd.extend(['docker','rm','-f',name])
    print(cmd)
    try:
        # stop container
        completed_process = subprocess.run(cmd,shell=False,capture_output=True)
        print(completed_process.stdout.decode())
        # Move artifacts to trash
        ## locally
        pm_root_dir = os.getenv('PM_ROOT_DIR',default='wd')
        src_path = '%s/service/%s'%(pm_root_dir,service_id)
        dst_path = '%s/trash/%s'%(pm_root_dir,trash_id)
        if os.path.exists(src_path):
            cmd=['mv','-f',src_path,dst_path]
            sp_out = subprocess.check_output(cmd)
        else:
            cmd=['mkdir','-p', dst_path]
            sp_out = subprocess.check_output(cmd)
            service_metadata=service['metadata']
            service_trash_metadata_path='%s/metadata.json'%(dst_path)
            with open(service_trash_metadata_path, 'w') as fp:
                json.dump(service_metadata,fp,indent=2)
        ## in s3
        #pm_s3_bucket = os.getenv('PM_S3_BUCKET',default='aws-do-pm')
        #cmd=['aws','s3','mv','s3://%s/service/%s'%(pm_s3_bucket,service_id),'s3://%s/trash/%s'%(pm_s3_bucket,trash_id)]
        #sp_out = subprocess.check_output(cmd)
    except subprocess.CalledProcessError as cpe:
        print(cpe.stderr)
        raise cpe

if __name__ == '__main__':

#    import debugpy; debugpy.listen(('0.0.0.0',5678)); debugpy.wait_for_client(); breakpoint()

    parser = argparse.ArgumentParser()
    parser.add_argument('--action', help='Service action: ls | describe | status | destroy')
    parser.add_argument('--id', help='Service id')
    parser.add_argument('--config', help='Service configuration template with provided values')
    args = parser.parse_args()
    action = args.action
    if (action == 'ls'): 
        list_services()
    elif (action == 'describe'):
        if (args.id is None):
            print("Please specify service id using the --id argument")
        else:
            describe_service(args.id)
    elif (action == 'status'):
        if (args.id is None):
            print("Please specify service id using the --id argument")
        else:
            check_service_status(args.id)
    elif (action == 'destroy'):
        if (args.config is None):
            print("Please specify service task config using the --config argument")
        else:
            destroy_service(args.config)
    else:
        print('Action %s not recognized'%action)
    
