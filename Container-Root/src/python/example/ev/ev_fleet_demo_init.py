import argparse
import os
import json
import subprocess
import lib.util.text_util as text_util
import sys
from multiprocessing import Process, Semaphore, Queue
import time
import random

# Default settings
data_path='wd/generated_ev_data'
num_vehicles=10
num_routes=10
num_predicted_routes=1
model_update_threshold=0.05
max_concurrent_tasks=10
pm_root_path=os.getenv('PM_ROOT_PATH',default='wd')
idx=int(os.getenv('IDX',default='1'))

# Global variables
raw_data_id = ""
base_model_id = ""

def clear_system():
    stty_sane()
    print("")
    print("=================================================================================")
    print("          Clearing system ...")
    print("=================================================================================")
    print("")
    completed_process = subprocess.run(['./pm system clear'],shell=True,capture_output=True,check=True)
    print(completed_process.stdout.decode())
    print(completed_process.stderr.decode())
    
def initialize_system():
    stty_sane()
    print("")
    print("=================================================================================")
    print("          Initializing system ...")
    print("=================================================================================")
    print("")
    completed_process = subprocess.run(['./pm system init'],shell=True,capture_output=True,check=True)
    print(completed_process.stdout.decode())
    print(completed_process.stderr.decode())
    
def register_technique(config_path, remote_path):
    stty_sane()
    print("")
    print("=================================================================================")
    print("          Registering custom technique for EV data selection  ...")
    print("=================================================================================")
    print("")
    
    cmd=["./cp-to.sh platform %s %s %s"%( str(idx), config_path, remote_path )]
    completed_process = subprocess.run(cmd,shell=True,capture_output=True,check=True)
    out=completed_process.stdout.decode()
    print(out)
    print(completed_process.stderr.decode())
    
    cmd=["./pm go register technique"]
    completed_process = subprocess.run(cmd,shell=True,capture_output=True,check=True)
    out=completed_process.stdout.decode()
    task_json=json.loads(out)
    task_json['analyticSettings']['config']=remote_path
    with open('/tmp/task_register_technique.json', 'w') as fp:
        json.dump(task_json,fp,indent=2)
    
    cmd=["./cp-to.sh platform %s %s %s"%(str(idx),"/tmp/task_register_technique.json","/tmp/task_register_technique.json")]
    completed_process = subprocess.run(cmd,shell=True,capture_output=True,check=True)
    out=completed_process.stdout.decode()
    print(out)
    print(completed_process.stderr.decode())
    
    cmd=["./pm do /tmp/task_register_technique.json"]
    completed_process = subprocess.run(cmd,shell=True,capture_output=True,check=True)
    out=completed_process.stdout.decode()
    print(out)
    print(completed_process.stderr.decode())
    
    
def stty_sane():
    cmd=['stty sane']
    completed_process = subprocess.run(cmd,shell=True,capture_output=True,check=True)
    
if __name__ == '__main__':

    #import debugpy; debugpy.listen(('0.0.0.0',5678)); debugpy.wait_for_client(); breakpoint()

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='Configuration file path, default: ./ev_fleet_demo.json')
    args = parser.parse_args()
    config_path = args.config
    if config_path is None:
        config_path = './ev_fleet_demo.json'

    
    # Check if config exists
    if os.path.exists(config_path):
        with open(config_path, 'r') as fp:
            config = json.load(fp)
            data_path=config['data_path']
            num_vehicles=config['num_vehicles']
            num_routes=config['num_routes']
            num_predicted_routes=config['num_predicted_routes']
            model_update_threshold=config['model_update_threshold']
            max_concurrent_tasks=config['max_concurrent_tasks']
    else:
        print("Specified config path %s does not exist"%config_path)
        print("Using default values.")
        
    # Show effective configuration
    print('')
    print('EV Fleet Configuation per Group:')
    print('data_path: %s'%data_path)
    print('num_vehicles: %s'%num_vehicles)
    print('num_routes: %s'%num_routes)
    print('num_predicted_routes: %s'%num_predicted_routes)
    print('model_update_threshold: %.2f'%model_update_threshold)
    print('max_concurrent_tasks: %s'%max_concurrent_tasks)
    print('')

    clear_system()
    initialize_system()
    register_technique('src/python/example/ev/technique/ev_data_select/technique_registration_ev_data_select.json', '/tmp/technique_registration_ev_data_select.json')
        
