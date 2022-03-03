######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

from multiprocessing import Process, Semaphore, Queue
import subprocess
import pm.service.service as service 
import time
import os

idx=int(os.getenv('IDX',default='1'))
if os.path.exists('.idx'):
    with open ('.idx', 'r') as fp:
        line=fp.readline()
        idx=line.strip()
    fp.close()

#def trigger_service_destroy(service_id,sema,queue):
def trigger_service_destroy(service_id):
    print("")
    print("=================================================================================")
    print("  Destroying service id %s"%(service_id) )
    print("=================================================================================")
    print("")
	
    cmd = ['./pm service destroy %s'%(service_id)]
    completed_process = subprocess.run(cmd,shell=True,capture_output=True,check=False)
    out = completed_process.stdout.decode()
    return_code=completed_process.returncode
    print(out)
    print(completed_process.stderr.decode())
    #queue.put(
    #    {
    #        'service_id': service_id,
    #        'return_code': return_code
    #        
    #    }
    #)
    #sema.release()

if __name__ == '__main__':

    num_services=0
    try:
        service_ids,service_map = service.list_services(verbose=False)
        num_services = len(service_ids)
    except:
        print("Warning: could not aquire list of services")

    if num_services > 0:    
        #sema = Semaphore(num_services)
        #queue = Queue()
        all_processes = []
        for service_id in service_ids:
            time.sleep(0.25)
            #sema.acquire()
            service_metadata = service_map[service_id]
            group_id = service_metadata['group_id']
            if (group_id == idx) or (group_id == ''):
                #p = Process(target=trigger_service_destroy, args=[service_id,sema,queue])
                p = Process(target=trigger_service_destroy, args=[service_id])
                all_processes.append(p)
                p.start()
            
        for p in all_processes:
            p.join()
            
        #result_list = [queue.get() for i in range(queue.qsize())]
        #result_map = {x['service_id']:x['return_code'] for x in result_list}
        #print(result_map)
        