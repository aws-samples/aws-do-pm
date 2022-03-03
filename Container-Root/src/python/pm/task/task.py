######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import argparse
import copy
import json
import os

import subprocess
import time
from datetime import datetime
from pathlib import Path
import lib.db.graph.data as graphdata
import lib.db.graph.dba as dba
from lib.util.dict_util import replace_keywords, dict_merge
import lib.util.file_util as file_util
import lib.uid_generator as uid_generator
import lib.util.list_util as list_util

graph = dba.get_graph()


def create_task(config, execute=True, ignore_key_list=[], verbose=True):
    #import debugpy; debugpy.listen(('0.0.0.0',5678)); debugpy.wait_for_client(); breakpoint()
    task_properties = {}
    if os.path.exists(config):
        with open(config, 'r') as fp:
            try:
                task_properties = json.load(fp)
            except json.decoder.JSONDecodeError as jde:
                print("exception=\n%s"%jde)
                print("config=\n%s"%config)
                fp.seek(0)
                print("content=\n%s"%fp.read())
        fp.close()    
        technique_name = task_properties['technique_name']
        # Get the technique json
        technique = graphdata.find_vertex('technique', 'technique_name', technique_name, graph, skip=0, limit=1)
        if len(technique) > 0:
            technique=technique[0]
            task_template = technique["task_template"]
            
            # Merge task_properties into task_template
            task_properties_merged = copy.deepcopy(task_template)
            dict_merge(task_properties_merged, task_properties)
    
            # Never replace anything under key "task_template"
            ignore_key_list.append("task_template")
    
            # Scan through config and fill in any <newid> and <timestamp> values        
            task_properties_updated = replace_keywords(task_properties_merged)
    
            # Inherit task settings from technique 
            to = os.getenv('TO', default='docker')
            registry = os.getenv('REGISTRY', default='')
            if registry != '':
                last_char = registry[-1]
                if last_char != '/':
                    registry.append('/')
            container_image = technique['task_container_image']                
            container_image_with_registry='%s%s'%(registry,container_image)
            task_to = technique['task_target_orchestrator']
            if ('python' != task_to):
                task_to=to
            task_properties_updated['target_orchestrator'] = task_to
            task_properties_updated['container_image'] = container_image_with_registry
            task_properties_updated['executor_filepath'] = technique['task_executor_filepath']
    
            # Construct task folder: ${PM_ROOT_PATH}/task/<task_id>
            cur_task_id = task_properties_updated['task_id']
            task_vertex = graphdata.get_vertex('task',cur_task_id,graph)
            if not task_vertex is None:
                print("Warning: Task %s already exists"%cur_task_id)
                cur_task_id=uid_generator.generate()
                print("Setting new task_id to %s"%cur_task_id)
                task_properties_updated['task_id'] = cur_task_id
                
            pm_root_path = os.getenv('PM_ROOT_PATH', default='wd').strip()
            task_input_json_filepath_full = '%s/task/%s/task.json' % (pm_root_path, cur_task_id)    
            out_file_path = Path(task_input_json_filepath_full)
            out_file_path.parent.mkdir(exist_ok=True, parents=True)
    
            # Write task json to folder
            with open(task_input_json_filepath_full, 'w') as fp:
                json.dump(task_properties_updated,fp)
                fp.flush()
                os.fsync(fp.fileno())
            fp.close()
    
            # Write task metadata
            metadata_path = '%s/task/%s/metadata.json' % (pm_root_path, cur_task_id)
            metadata={'node_name': task_properties_updated['node_name'], 'metadata': {'task':task_properties_updated,'return_code': '', 'stdout': '', 'stderr': ''}}
            file_util.write_json(metadata_path,metadata)
    
            graphdata.insert_vertex('task',cur_task_id, metadata , graph)

            # Link task to technique
            technique_keys = graphdata.find_vertex_key('technique','technique_name',technique_name,graph,0,1)
            technique_key = technique_keys[0]
            graphdata.insert_edge('link','technique/%s'%technique_key,'task/%s'%cur_task_id,graph)
    
            # Link input_artifacts to task
            input_artifacts = task_properties_updated['input_artifacts']
            for k,v in input_artifacts.items():
                for cur_v in v:
                    from_id='%s/%s'%(k,cur_v)
                    to_id='task/%s'%cur_task_id
                    if verbose:
                        print("Task: inserting edge from %s to %s"%(from_id,to_id))
                    graphdata.insert_edge('link',from_id,to_id,graph)
    
            # print the task_id we created
            print('task/%s'%cur_task_id)
    
            if execute:
                time.sleep(0.5)
                execute_task(cur_task_id)
        else:
            print("Error: technique %s not found."%technique_name)
    else:
        print("Error: task config path %s does not exist"%config)

def execute_task(task_id):
    # Get the task json
    pm_root_path = os.getenv('PM_ROOT_PATH',default='wd').strip()
    task_input_json_filepath_full = '%s/task/%s/task.json'%(pm_root_path, task_id)
    print("Executing task from %s ..."%task_input_json_filepath_full)
    sp_out=""
    if os.path.exists(task_input_json_filepath_full):
        with open(task_input_json_filepath_full, 'r') as fp:
            task_json = json.load(fp)
            fp.flush()
        fp.close()
    
        # Get execution details
        target_orchestrator = task_json['target_orchestrator']
        container_image = task_json['container_image']
        task_executor_filepath = task_json['executor_filepath']
        task_options = task_json['task_options']
    
        # Compose the command line
        exec_cmd=""
        processor = os.getenv("PROCESSOR", default="cpu")
        if 'processor' in task_json:
            task_processor = task_json['processor']
            if task_processor in ['cpu','gpu','inf']:
                processor = task_processor
        if (target_orchestrator=='python'):
            exec_cmd = ['python',
                    task_executor_filepath,
                    "--config",
                    task_input_json_filepath_full]
        elif (target_orchestrator=='docker'):
            vol_map = os.getenv('VOL_MAP',default="")
            port_map = os.getenv('PORT_MAP',default="")
            exec_cmd_tmp = ['docker', 'run']
            if len(task_options) > 0:
                for opt in task_options:
                    if opt not in ['--pod-running-timeout=90s','--restart=Always','--restart=Never','--restart=OnFailure']:
                        exec_cmd_tmp.append(opt) 
            if processor == "gpu":
                exec_cmd_tmp.append("--gpus=all")
            
            exec_cmd_tmp2 = [vol_map, port_map, '--network aws-do-pm_default', container_image,
            'python', task_executor_filepath, '--config', task_input_json_filepath_full]
            for opt in exec_cmd_tmp2:
                exec_cmd_tmp.append(opt)
    
            exec_cmd = list(list_util.splitWords(exec_cmd_tmp))
            #exec_cmd = exec_cmd_tmp
        elif (target_orchestrator=='kubernetes'):
            efs_wd_pvc_name = os.getenv('EFS_WD_PVC_NAME', default='pm-efs-wd-pvc')
            namespace = os.getenv('NAMESPACE', default='aws-do-pm')
            exec_cmd_tmp = ['kubectl', '-n',namespace,'run']
            if len(task_options) > 0:
                for opt in task_options:
                    if opt in ['-it','-i','-t','--rm','--pod-running-timeout=90s','--restart=Always','--restart=Never','--restart=OnFailure']:
                        exec_cmd_tmp.append(opt) 
                        
            pod_name = 'task-%s'%(task_id)
            override_dict = {
                "metadata": {
                    "labels": {
                        "app": "aws-do-pm",
                        "role": "task"
                    },
                },
                "spec": {
                    "topologySpreadConstraints": [
                        {
                            "labelSelector": {
                                "matchLabels": {
                                    "role": "task"
                                }
                            },
                            "maxSkew": 1,
                            "topologyKey": "kubernetes.io/hostname",
                            "whenUnsatisfiable": "ScheduleAnyway"
                        }
                    ],                
                    "containers": [{
                        "name": "%s"%pod_name,
                        "image": "%s"%container_image,
                        "imagePullPolicy": "Always",
                        "command": ["python"],
                        "args": [task_executor_filepath, '--config', task_input_json_filepath_full],
                        "resources": {},
                        "volumeMounts": [{
                            "mountPath": "/wd",
                            "name": "wd"
                        }]
                    }],
                    "volumes": [{
                        "name": "wd",
                        "persistentVolumeClaim": {
                            "claimName": "pm-efs-wd-pvc"
                        }
                    }],
                    "imagePullSecrets": [
                        {
                            "name": "regcred"
                        }
                    ]                    
                }
            }

            if processor == "gpu":
                override_dict["spec"]["containers"][0]["resources"]={"limits":{"nvidia.com/gpu": "1"}}
            
            override_json=json.dumps(override_dict)
            #print(volume_json)
            exec_cmd_tmp2 = []
            if '-d' not in task_options:
                exec_cmd_tmp2.extend(['--wait=true','--grace-period=10'])
            else:
                exec_cmd_tmp2.extend(['--wait=false'])
            exec_cmd_tmp2.extend([pod_name,'--image',container_image,'--overrides',override_json])
            for opt in exec_cmd_tmp2:
                    exec_cmd_tmp.append(opt)
            exec_cmd = list(list_util.splitWords(exec_cmd_tmp))
        else:
            print('Target operator %s not supported'%target_orchestrator)
    
        sp_out=""
        sp_err=""
        sp_code=0
        try:
            # 1. Execute task using subprocess.run([])
            print("Executing PM task:")
            print(exec_cmd)
            completed_process = subprocess.run(exec_cmd,shell=False,capture_output=True,check=True)
            sp_out = completed_process.stdout.decode()
            sp_err = completed_process.stdout.decode()
            sp_code = completed_process.returncode
            # 2. Create nodes for the output artifacts
            # 3. Create edges from the task to the destination nodes
            output_artifacts = task_json['output_artifacts']
            for k,v in output_artifacts.items():
                for cur_v in v:
                    print('%s/%s'%(k,cur_v))
                    artifact_properties = get_artifact_properties(k,cur_v,timeout_sec=180)
                    vertex = graphdata.get_vertex(k,cur_v,graph)
                    if vertex is None:
                        graphdata.insert_vertex(k,cur_v, artifact_properties , graph)
                    graphdata.insert_edge('link','task/%s'%task_json['task_id'],'%s/%s'%(k,cur_v),graph)
        except subprocess.CalledProcessError as cpe:
            # Failure
            sp_out = cpe.stdout.decode()
            sp_err = cpe.stderr.decode()
            sp_code = cpe.returncode
            print(sp_out)
            print(sp_err)
            # Create Error Node
            error_properties={'node_name': 'error', 'created_dt': datetime.now().strftime('%Y%m%d-%H%M%S-%f'),'task':task_json['task_id'],'cmd':exec_cmd,'stdout':sp_out,'stderr':sp_err, 'return_code': sp_code}
            create_error(task_json,error_properties)
        except Exception as e:
            # Failure
            print("Subprocess call failed: %s"%exec_cmd)
            # Create Error Node
            error_id = uid_generator.generate()
            error_properties = {'node_name': 'error', 'created_dt': datetime.now().strftime('%Y%m%d-%H%M%S-%f'),'task':task_json['task_id'], 'cmd': exec_cmd, 'error': str(e)}
            create_error(task_json,error_properties)
            sp_out=str(e)
            sp_code = -1
    
        print('Return code: %s'%(str(sp_code)))
        print(sp_out)
        #print(sp_err)
    
        update_task_metadata(task_id,sp_code,sp_out,sp_err)
    else:
        print("Error: Task path %s not found"%task_input_json_filepath_full)

    return sp_out

def update_task_metadata(task_id,sp_code,sp_out,sp_err):
    pm_root_path = os.getenv('PM_ROOT_PATH', default='wd')
    metadata_path = '%s/task/%s/metadata.json' % (pm_root_path, task_id)
    metadata = file_util.read_json(metadata_path)
    metadata['metadata']['return_code'] = sp_code
    metadata['metadata']['stdout'] = sp_out
    metadata['metadata']['stderr'] = sp_err
    file_util.write_json(metadata_path,metadata)
    graphdata.update_vertex('task','task/%s'%task_id,metadata,graph)

def create_error(task_properties, error_properties):
    error_id = uid_generator.generate()
    #print('Inserting error properties into graph')
    #print(error_properties)
    graphdata.insert_vertex('error',error_id,error_properties,graph)
    graphdata.insert_edge('link','task/%s'%task_properties['task_id'],'error/%s'%error_id,graph)

def get_artifact_properties(type,id,timeout_sec=6):
    pm_root_path = os.getenv('PM_ROOT_PATH', default='wd')
    artifact_json_folder = '%s/%s/%s'%(pm_root_path,type,id)
    artifact_json_filepath = '%s/metadata.json' % (artifact_json_folder)
    artifact_properties={"metadata":{}}
    # Wait up to timeout_sec for artifact_json_filepath to become available
    time_start = time.time()
    while (not os.path.exists(artifact_json_filepath)) and (time.time()-time_start <= timeout_sec):
        print("Task is waiting for %s ..."%artifact_json_filepath)
        time.sleep(3)

    if os.path.exists(artifact_json_filepath):
        with open(artifact_json_filepath,'r') as fp:
            artifact_properties = json.load(fp)
    else:
        print("Timeout: Task timed out after %s sec while waiting for %s"%(timeout_sec,artifact_json_filepath))
    if "node_name" not in artifact_properties:
        artifact_properties["node_name"] = type
    if "created_dt" not in artifact_properties:
        artifact_properties["created_dt"] = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    return artifact_properties  

def list_tasks():
    tasks = graphdata.get_vertices('task', graph)
    task_list = []
    c = tasks.all()
    while (not c.empty()):
        t = c.next()
        task_list.append(t['metadata']['task']['task_id'])
        print('%s %s'%(t['metadata']['task']['task_id'],t['node_name']))
    return task_list

def describe_task(task_id):
    task = graphdata.get_vertex('task', task_id, graph)
    print(json.dumps(task, indent=2))

def delete_task(task_id):
    task = graphdata.get_vertex('task','task/%s'%task_id,graph)
    trash = dba._create_get_vertex_collection(graph,'trash',verbose=False)
    trash_id=uid_generator.generate_uid()
    deleted_task={'metadata':task}
    graphdata.insert_vertex('trash','trash/%s'%trash_id,deleted_task,graph)
    graphdata.insert_edge('link','task%s'%task_id,'trash/%s'%trash_id,graph)
    return trash_id

def interrupt_task(task_id):
    task = 2

def task_status(task_id):
    print("status")

def export_task_template(technique_id, config):
    technique = graphdata.get_vertex('technique', technique_id, graph)
    task_template = json.dumps(technique['task_template'], indent=2)
    path = os.path.dirname(config)
    os.makedirs(path,exist_ok=True)
    with open(config, 'w') as fp:
        fp.write(task_template)     

    print(os.path.abspath(config))   
    return task_template

if __name__ == '__main__':

    """
        ls                                                  - list all tasks
        describe <task_id>                                  - display task metadata
        template <technique_id> <task_local_json_filepath>  - generate task template and save it in a local file
        create <task_local_json_filepath>                   - create a task from a local file and do not execute it
        delete <task_id>                                    - delete a task that was created but not executed
        exec <task_id>                                      - execute a task that was created but not executed
        run <task_local_json_filepath>                      - create a task from a local file and then execute it
        status <task_id>                                    - show current task status
        interrupt <task_id>                                 - interrupt a running task
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('--action', help='Task action: ls | describe | create | delete | exec | run | status | interrupt ')
    parser.add_argument('--task_id', help='Task unique identifier')
    parser.add_argument('--technique_id', help="Technique unique identifier when needed by subcommand")
    parser.add_argument('--config', help='Path to task configuration json')
    args = parser.parse_args()
    action = args.action
    if (action == 'ls'):
        list_tasks()
    elif (action == 'describe'):
        if (args.task_id is None):
            print("Please specify task_id using the --task_id argument")
        else:
            describe_task(args.task_id)
    elif (action == 'template'): 
        if (args.technique_id is None):
            print("Please specify technique name using the --technique artument")
        elif (args.config is None):
            print("Please specify template export path using the --config argument")
        else:
            export_task_template(args.technique_id, args.config)
    elif (action == 'delete'):
        if (args.task_id is None):
            print("Please specify task_id using the --task_id argument")
        else:
            delete_task(args.task_id)
    elif (action == 'exec'):
        if (args.task_id is None):
            print("Please specify task_id using the --task_id argument")
        else:
            execute_task(args.task_id)
    elif (action == 'status'):
        if (args.task_id is None):
            print("Please specify task_id using the --task_id argument")
        else:
            task_status(args.task_id)
    elif (action == 'run'):
        if (args.config is None):
            print("Please specify task path using the --config argument")
        else:
            create_task(args.config, execute=True)
    elif (action == 'interrupt'):
        if (args.task_id is None):
            print("Please specify task_id using the --task_id argument")
        else:
            interrupt_task(args.task_id)
    elif (action == 'create'):
        if (args.config is None):
            print("Please specify task config path using the --config argument")
        else:
            create_task(args.config, execute=False)
    else:
        print('Action %s not recognized' % action)
