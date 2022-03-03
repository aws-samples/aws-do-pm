import argparse
import os
import json
import subprocess
import lib.util.text_util as text_util
import sys
from multiprocessing import Process, BoundedSemaphore, Queue
import time
import random
from datetime import datetime

# Default settings
data_path='wd/generated_ev_data'
num_vehicles=10
num_routes=10
num_predicted_routes=1
model_update_threshold=0.05
max_concurrent_tasks=10
pm_root_path=os.getenv('PM_ROOT_PATH',default='wd')
uid_length_env = os.getenv('PM_ID_LENGTH', default='32')
uid_length = int(uid_length_env)

idx=int(os.getenv('IDX',default='1'))
if os.path.exists('.idx'):
    with open ('.idx', 'r') as fp:
        line=fp.readline()
        idx=line.strip()
    fp.close()
    
# Global variables
raw_data_id = ""
base_model_id = ""
start_time = None
end_time = None

def demo_start(num_vehicles, num_routes):
    stty_sane()
    print("")
    print("=================================================================================")
    print("                             %s"%(datetime.now()))
    print("                               Group %s"%idx)
    print("                          Executing EV Fleet Demo ")
    print("                         for %s electric vehicles "%num_vehicles)
    print("                 driving minimum %s and maximum %s routes each "%(round(num_routes/2),num_routes))
    print("=================================================================================")
    print("")
    global start_time
    start_time = time.time()
    
def generate_ev_data(group_data_path,num_vehicles,num_routes):
    stty_sane()
    if os.path.exists(group_data_path):
        print("")
        print("Generated data found in path %s"%group_data_path)
        print("Skipping data generation")
        print("")
    else:
        print("")
        print("=================================================================================")
        print("                               Group %s"%idx)
        print("       Generating Electric Vehicle data for %s vehicles, %s routes each ..."%(num_vehicles,num_routes))
        print("=================================================================================")
        print("")

		# Login to Docker registry if needed
        completed_process = subprocess.run('./login.sh',shell=False,capture_output=True,check=True)
        print(completed_process.stdout.decode())
        print(completed_process.stderr.decode())
		
		# Execute data generation in container
        cmd=["docker","run","-it","--rm","-v","%s/wd:/wd"%os.getenv('PROJECT_HOME',default=os.getcwd()),"-e","NUM_VEHICLES=%s"%num_vehicles,"-e","NUM_ROUTES=%s"%num_routes,"-e","DEST_PATH=%s"%group_data_path,"%saws-do-pm-ev_datagen_em%s"%(os.getenv('REGISTRY',default=''),os.getenv('TAG',default=':latest')),"/bin/bash","-c","/src/python/example/ev/task/ev_data_generate.sh"]		
        if os.getenv('VERBOSE',default='false') == "true":
            print(cmd)
		
        completed_process = subprocess.run(cmd,shell=False,capture_output=True,check=True)
        print(completed_process.stdout.decode())
        print(completed_process.stderr.decode())
    
def register_dataset(group_data_path,main_file_name,description):
    stty_sane()
    print("")
    print("=================================================================================")
    print("                               Group %s"%idx)
    print("          Registering data set from path %s ..."%group_data_path)
    print("          Main file: %s"%main_file_name)
    print("          Description: %s"%description)
    print("=================================================================================")
    print("")

    cmd=['./pm data register %s %s "%s"'%(group_data_path, main_file_name, description)]
    completed_process = subprocess.run(cmd,shell=True,capture_output=True,check=True)
    print(completed_process.stdout.decode())
    print(completed_process.stderr.decode())
    
    out=completed_process.stdout.decode()
    
    lines=text_util.exclude_lines(out,['load','path','python','edge'])
    line=text_util.include_lines(lines,['data'])
    data_id_token=text_util.extract_token(line,'/',1)
    data_id=text_util.trim_token(data_id_token)
    print("DATA_ID=%s"%data_id)    
    return data_id
    
def build_model(data_id):
    stty_sane()
    print("")
    print("=================================================================================")
    print("                               Group %s"%idx)
    print("          Building Neural Network model using DATA_ID %s ..."%data_id)
    print("=================================================================================")
    print("")

    cmd=["./pm model build %s"%(data_id)]
    completed_process = subprocess.run(cmd,shell=True,capture_output=True,check=True)
    out=completed_process.stdout.decode()
    print(out)
    print(completed_process.stderr.decode())
    lines = text_util.exclude_lines(out,['ported','sync','upload','edge'])
    line = text_util.include_lines(lines,['nitializing'])
    model_id_raw = text_util.extract_token(line,'/',2)
    model_id = text_util.trim_token(model_id_raw)
    print("MODEL_ID=%s"%model_id)
    return model_id
    
def deploy_model_service(model_id):
    stty_sane()
    print("")
    print("=================================================================================")
    print("                               Group %s"%idx)
    print("       Deploying model %s as a gRPC service ..."%(model_id))
    print("=================================================================================")
    print("")

    cmd=['./pm service deploy %s'%(model_id)]
    completed_process = subprocess.run(cmd,shell=True,capture_output=True,check=True)
    out=completed_process.stdout.decode()
    print(out)
    print(completed_process.stderr.decode())

    line = text_util.include_lines(out,['SERVICE_ID'])
    service_id_raw = text_util.extract_token(line,'=',1)
    service_id = text_util.trim_token(service_id_raw)
    print("SERVICE_ID=%s"%service_id)
    return service_id
    
def select_data(raw_data_id, vehicle_id, route_num):
    stty_sane()
    print("")
    print("=================================================================================")
    print("                               Group %s"%idx)
    print("          Selecting new data for vehicle # %s, route # %s ..."%(vehicle_id,route_num) )
    print("=================================================================================")
    print("")
	
    selected_data_id = ''
    retry_cnt=0
    retry_max=3
    while (len(selected_data_id) != uid_length) and (retry_cnt < retry_max):
        retry_cnt = retry_cnt + 1
        try:
            cmd = ["./pm go select ev data"]
            completed_process = subprocess.run(cmd,shell=True,capture_output=True,check=True)
            out = completed_process.stdout.decode()
            print(completed_process.stderr.decode())
            task_str = out.replace("<data_id>",raw_data_id)
            task_str = task_str.replace("<vehicle_id>",str(vehicle_id))
            task_str = task_str.replace("<route_id>",str(route_num))
            task_json = json.loads(task_str)
            task_id = task_json['task_id']
            task_json_path_local = '%s/tmp/%s/task_%s_ev_data_select.json'%(pm_root_path.strip(),idx,task_id)
            task_json_path_container = "%s/tmp/%s/task_%s_ev_data_select.json"%(pm_root_path.strip(),idx,task_id)
            with open(task_json_path_local, 'w') as fp:
        	    json.dump(task_json,fp,indent=2)
            cmd = ["./cp-to.sh platform %s %s %s"%(str(idx),task_json_path_local,task_json_path_container)]
            completed_process = subprocess.run(cmd,shell=True,capture_output=True,check=True)
            out = completed_process.stdout.decode()
            print(out)
            print(completed_process.stderr.decode())
            time.sleep(1)
            cmd = ["./pm do %s"%(task_json_path_container)]
            completed_process = subprocess.run(cmd,shell=True,capture_output=True,check=True)
            out = completed_process.stdout.decode()
            print(out)
            print(completed_process.stderr.decode())
            lines = text_util.exclude_lines(out,['load','path','port','kubectl','datagen','xecuting','edge'])
            line = text_util.include_lines(lines,['data'])
            selected_data_id_raw = text_util.extract_token(line,'/',1)
            selected_data_id = text_util.trim_token(selected_data_id_raw)
            print("DATA_ID=%s"%selected_data_id)
        except Exception as e:
            print("Error: Group %s failed to select data for vehicle %s, route %s on try %s/%s"%(str(idx),vehicle_id,route_num,str(retry_cnt),str(retry_max)))
            print(e)
            time.sleep(random.randint(1,3))
    return selected_data_id
	
def predict(service_id, data_id):
    stty_sane()
    print("")
    print("=================================================================================")
    print("                               Group %s"%idx)
    print("  Predicting with model service %s and data %s ..."%(service_id,data_id))
    print("=================================================================================")
    print("")

    retry_cnt = 0
    retry_max = 3
    
    predicted_data_id=''
    prediction_error=-1

    while (retry_cnt < retry_max) and (len(predicted_data_id) != uid_length):
        retry_cnt=retry_cnt+1
        try:
            cmd = ['./pm model predict %s %s'%(service_id, data_id)]
            completed_process = subprocess.run(cmd,shell=True,capture_output=True,check=True)
            out = completed_process.stdout.decode()
            print(out)
            print(completed_process.stderr.decode())
            lines = text_util.exclude_lines(out,['s3://','kubectl','ported','edge'])
            line = text_util.include_lines(lines,['data'])
            print("selected line: %s"%line)
            if (line is None) or ("" == line.strip()):
                print("Error: could not find data output on try %s/%s"%(str(retry_cnt),str(retry_max)))
                print(out)
            else:
                predicted_data_id_raw = text_util.extract_token(line,'/',1)
                predicted_data_id = text_util.trim_token(predicted_data_id_raw)
                print("DATA_ID=%s"%predicted_data_id)        
            if len(predicted_data_id) != uid_length:
                prediction_error=-1
            else:
                cmd = ['./pm data describe %s'%(predicted_data_id)]
                completed_process = subprocess.run(cmd,shell=True,capture_output=True,check=True)
                out = completed_process.stdout.decode()
                print(completed_process.stderr.decode())
                data_json = json.loads(out)
                prediction_error = data_json['mae_overall']
                print("PREDICTION_ERROR=%.2f"%prediction_error)
        except Exception as e:
            print("Error: Group %s failed to predict with service %s and data %s on try %s/%s"%(str(idx),service_id,data_id,str(retry_cnt),str(retry_max)))
            print(e)
            time.sleep(random.randint(1,3))
    	
    return predicted_data_id,prediction_error
	
def update_model(service_id, data_id):
    try_cnt=0
    retry_max=3
    updated_model_id=''
    while (len(updated_model_id) != uid_length) and (try_cnt <= retry_max):
        try:
            try_cnt = try_cnt+1
            stty_sane()
            print("")
            print("=================================================================================")
            print("                               Group %s"%idx)
            print("          Updating model/service %s using data %s ..."%(service_id,data_id) )
            print("=================================================================================")
            print("")
        
            cmd = ['./pm model update %s %s'%(service_id, data_id)]
            completed_process = subprocess.run(cmd,shell=True,capture_output=True,check=True)
            out = completed_process.stdout.decode()
            print(out)
            print(completed_process.stderr.decode())
            lines = text_util.exclude_lines(out,['metadata','kubectl','upload','ported','edge'])
            line = text_util.include_lines(lines,['model'])
            updated_model_id_raw = text_util.extract_token(line,'/',1)
            updated_model_id = text_util.trim_token(updated_model_id_raw)
        except Exception as e:
            print("Error: Group %s failed to update service %s with data %s on try %s/%s"%(str(idx),service_id,data_id,str(try_cnt),str(retry_max)))
            print(e)
            time.sleep(random.randint(1,3))
            
    print("UPDATED_MODEL_ID=%s"%updated_model_id)
    return updated_model_id

def configure_service(service_id,model_id):
    stty_sane()
    print("")
    print("=================================================================================")
    print("                               Group %s"%idx)
    print("Configuring service id %s with model %s"%(service_id,model_id) )
    print("=================================================================================")
    print("")
	
    cmd = ['./pm service configure %s %s'%(service_id, model_id)]
    completed_process = subprocess.run(cmd,shell=True,capture_output=True,check=True)
    out = completed_process.stdout.decode()
    print(out)
    print(completed_process.stderr.decode())

def launch_digital_twin_service(model_id, vehicle_id, queue):
    print("Deploying Digital Twin for Group %s Vehicle %s ..."%(idx,vehicle_id))    
    out_service_id = deploy_model_service(model_id=model_id)
    queue.put(
        {
            'vehicle_id': vehicle_id,
            'model_id': model_id,
            'service_id': out_service_id
        }
    )
def run_digital_twin(service_id,vehicle_id):
    print("Running Digital Twin for Group %s Vehicle %s ..."%(idx,vehicle_id))
    vehicle_num_routes = random.randint(round(num_routes/2),num_routes)
    print("Group %s vehicle %s will run for %s routes"%(str(idx),vehicle_id,str(vehicle_num_routes)))
    for r in range(0,vehicle_num_routes):
        for pr in range(0,num_predicted_routes):
            time.sleep(0.5)
            route_num=r+pr
            route_data_id=select_data(raw_data_id, vehicle_id, route_num)
            predicted_data_id,prediction_error = predict(service_id,route_data_id)
            if prediction_error > model_update_threshold:
                print("VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV")
                print("Updating model for group %s vehicle %s ..."%(idx,vehicle_id))
                updated_model_id = update_model(service_id, route_data_id)
                configure_service(service_id,updated_model_id)

def deploy_digital_twins_parallel():
    queue = Queue()
    all_processes = []
    for cur_idx in range(num_vehicles):
        time.sleep(0.5)
        p = Process(target=launch_digital_twin_service, args=[base_model_id, cur_idx, queue])
        all_processes.append(p)
        p.start()
    
    result_list = [queue.get() for p in all_processes]
    for p in all_processes:
        p.join()

    service_map = {x['vehicle_id']:x['service_id'] for x in result_list}
    return service_map
    
def run_digital_twins_parallel(dt_map):
    all_processes = []    
    
    for cur_idx in range(num_vehicles):
        time.sleep(0.5)
        service_id = dt_map[cur_idx]
        p = Process(target=run_digital_twin, args=[service_id, cur_idx])
        all_processes.append(p)
        p.start()
    
    for p in all_processes:
        p.join()
        
def decomission_digital_twins():
    stty_sane()
    print("")
    print("=================================================================================")
    print("                               Group %s"%idx)
    print("                      Decomissioning Digital Twins ... ")
    print("=================================================================================")
    print("")
	
    cmd=['./exec.sh platform %s python src/python/pm/service/services_destroy.py'%(str(idx))]
    completed_process = subprocess.run(cmd,shell=True,capture_output=True,check=True)
    out = completed_process.stdout.decode()
    print(out)
    print(completed_process.stderr.decode())

#def demo_end(dt_run_map):
def demo_end():
    global start_time
    global end_time
    end_time = time.time()
    print("")
    print("=================================================================================")
    print("                               %s"%(datetime.now()))
    print("                               Group %s"%(str(idx)))
    print("                        EV Fleet Demo Completed ")
    print("")
    print("                            Elapsed %s minutes"%( int( (end_time-start_time)/60 ) ) )
    print("=================================================================================")
    print("")
    return 0
    
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
    print('EV Group Configuration:')
    print('data_path: %s'%data_path)
    print('num_vehicles: %s'%num_vehicles)
    print('num_routes: %s'%num_routes)
    print('num_predicted_routes: %s'%num_predicted_routes)
    print('model_update_threshold: %.2f'%model_update_threshold)
    print('max_concurrent_tasks: %s'%max_concurrent_tasks)
    print('')

    demo_start(num_vehicles,num_routes)
    
    group_data_path='%s_v%s_r%s_%s'%(data_path,num_vehicles,num_routes,idx)
    generate_ev_data(group_data_path, num_vehicles, num_routes)
    raw_data_id = register_dataset(group_data_path,'overall_pd.csv','Raw EV fleet dataset for %s vehicles and %s routes'%(num_vehicles,num_routes))
    train_data_id = register_dataset('%s/train_data'%group_data_path,'input_output.json','EV model training dataset')
    base_model_id = build_model(train_data_id)
    dt_map = deploy_digital_twins_parallel()
    run_digital_twins_parallel(dt_map)
    decomission_digital_twins()
    
    demo_end()
