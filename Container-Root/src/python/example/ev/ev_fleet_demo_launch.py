import argparse
import os
import json
import subprocess
import lib.util.text_util as text_util
import sys
from multiprocessing import Process, Semaphore, Queue
import time
import random
from datetime import datetime

# Default settings
pm_root_path=os.getenv('PM_ROOT_PATH',default='wd')

idx=int(os.getenv('IDX',default='1'))
if os.path.exists('.idx'):
    with open ('.idx', 'r') as fp:
        line=fp.readline()
        idx=line.strip()
    fp.close()
    
# Global variables
start_time = None
end_time = None


def launch_group(group_id,config_path):
    stty_sane()
    print("")
    print("=================================================================================")
    print("          Launching EV Group %s ..."%group_id)
    print("=================================================================================")
    print("")

    cmd=["./exec.sh platform %s python src/python/example/ev/ev_fleet_demo.py --config %s"%(str(group_id),config_path)]
    with subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE) as group_subprocess:
        for line in group_subprocess.stdout:
            print(line.decode())
    return_code = group_subprocess.returncode
    group_subprocess.poll()
    group_subprocess.communicate()
    if return_code != 0:
        print("Group %s return code: %s"%(group_id,return_code))

def launch_groups_parallel(config_path,num_groups):
    all_processes = []    
    
    for cur_idx in range(1,num_groups+1):
        time.sleep(1)
        p = Process(target=launch_group, args=[cur_idx,config_path])
        all_processes.append(p)
        p.start()
    
    for p in all_processes:
        p.join()
        

def stty_sane():
    cmd=['stty sane']
    completed_process = subprocess.run(cmd,shell=True,capture_output=True,check=True)
    
if __name__ == '__main__':

    #import debugpy; debugpy.listen(('0.0.0.0',5678)); debugpy.wait_for_client(); breakpoint()

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='Configuration file path, default: ./ev_fleet_demo.json')
    parser.add_argument('--groups', help='Number of vehicle groups in the fleet, default: 1')
    args = parser.parse_args()
    config_path = args.config
    if config_path is None:
        config_path = './ev_fleet_demo.json'
        
    num_groups_str = args.groups
    num_groups = 1
    if not num_groups_str is None:
        try:
            num_groups = int(num_groups_str)
        except ValueError as ve:
            print("Invalid number of groups (%s) "%num_groups_str)
            print("Launching single group ...")
            
    launch_groups_parallel(config_path,num_groups)