import configparser
from itertools import chain, repeat

import boto3
import numpy as np

# from ga_definition import n_population, n_generation
# from ga_definition import vcpu, memory, ce1_batch_job_queue, batch_job_definition

# https://stackoverflow.com/questions/23294658/asking-the-user-for-input-until-they-give-a-valid-response
valid_options = ['y', 'Y']
prompts = chain(["Enter (y/Y) to Launch Batch Job: "], repeat("No Match; Try again: "))
replies = map(input, prompts)
valid_response = next(filter(valid_options.__contains__, replies))

config = configparser.RawConfigParser()
config.read('./template/config_template.conf')
common_dict = config._sections['common']
ga_dict = config._sections['GA']

region_name = common_dict['region_name']
vcpu = int(ga_dict['vcpu'])
memory = int(ga_dict['memory'])
job_queue = ga_dict['job_queue']
batch_job_definition = ga_dict['batch_job_definition']
n_population = int(ga_dict['n_population'])
n_generation = int(ga_dict['n_generation'])
resource_requirements = [
    {
        'type': 'VCPU',
        'value': str(vcpu)
    },
    {
        'type': 'MEMORY',
        'value': str(memory)
    },
    {
        'type': 'GPU',
        'value': str(1)
    }
]

batch_client = boto3.client('batch', region_name=region_name)

skip_lhs_setup = False

if (not skip_lhs_setup):
    # Initialize the LHS into the database
    env_vars = [
    ]
    # Evalute and Store in Database
    command = ["python",
               "ga_step0_job.py"]
    container_overrides = {
        # 'vcpus': vcpu,
        # 'memory': memory,
        'environment': env_vars,
        'command': command,
        'resourceRequirements': resource_requirements
    }
    print('Launching LHS Candidate Selection Single Job: Initial Seeding')
    resp = batch_client.submit_job(
        jobName='setup_lhs_candidates',
        jobQueue=job_queue,
        jobDefinition=batch_job_definition,
        containerOverrides=container_overrides
    )

    # print(resp)
    jobid_lhs_sample_create = resp['jobId']

    # Launch the as Array Job
    env_vars = [
        {"name": "POPULATION", "value": 'population'},
        {"name": "GENERATION", "value": str(0)},
        {"name": "NUMBA_NUM_THREADS", "value": str(vcpu)}
    ]

    # Evalute and Store in Database
    command = ["python",
               "ga_batcheval_job.py"]
    container_overrides = {
        # 'vcpus': vcpu,
        # 'memory': memory,
        'environment': env_vars,
        'command': command,
        'resourceRequirements': resource_requirements
    }

    print('Launching LHS Candidate Evaluation Array Job')

    resp = batch_client.submit_job(
        jobName='batcheval_lhs',
        jobQueue=job_queue,
        arrayProperties={'size': n_population},
        jobDefinition=batch_job_definition,
        containerOverrides=container_overrides,
        dependsOn=[{'jobId': jobid_lhs_sample_create}]
    )

    jobid_lhs_sample_eval = resp['jobId']

# At this point the GA is setup
for i_generation in np.arange(n_generation):
    if (i_generation == 0):
        if not skip_lhs_setup:
            prev_jobid = jobid_lhs_sample_eval

    # Generate the offsprings
    env_vars = [
        {"name": "GENERATION", "value": str(i_generation)},
    ]

    # Evalute and Store in Database
    command = ["python",
               "ga_genoffspring_job.py"]
    container_overrides = {
        # 'vcpus': vcpu,
        # 'memory': memory,
        'environment': env_vars,
        'command': command,
        'resourceRequirements': resource_requirements
    }

    print('Generation: %d, Generate OffSpring Single Job')
    if (i_generation == 0) & (skip_lhs_setup):
        dependsOn = []
    else:
        dependsOn = [{'jobId': prev_jobid}]
    resp = batch_client.submit_job(
        jobName='genoffspring_%d' % (i_generation),
        jobQueue=job_queue,
        jobDefinition=batch_job_definition,
        containerOverrides=container_overrides,
        dependsOn=dependsOn
    )

    prev_jobid = resp['jobId']
    # Run the Batch Job to evaluate offspring
    env_vars = [
        {"name": "POPULATION", "value": 'offspring'},
        {"name": "GENERATION", "value": str(i_generation)},
        {"name": "NUMBA_NUM_THREADS", "value": str(vcpu)}
    ]

    # Evalute and Store in Database
    command = ["python",
               "ga_batcheval_job.py"]
    container_overrides = {
        # 'vcpus': vcpu,
        # 'memory': memory,
        'environment': env_vars,
        'command': command,
        'resourceRequirements': resource_requirements
    }

    print('Generation: %d, Evaluate Offspring Array Job')
    resp = batch_client.submit_job(
        jobName='batchevaloffspring_%d' % (i_generation),
        jobQueue=job_queue,
        arrayProperties={'size': n_population},
        jobDefinition=batch_job_definition,
        containerOverrides=container_overrides,
        dependsOn=[{'jobId': prev_jobid}]
    )

    prev_jobid = resp['jobId']
    # Perform the mixing and create next generation
    env_vars = [
        {"name": "GENERATION", "value": str(i_generation)},
    ]

    # Evalute and Store in Database
    command = ["python",
               "ga_mixcreatenextgen_job.py"]
    container_overrides = {
        # 'vcpus': vcpu,
        # 'memory': memory,
        'environment': env_vars,
        'command': command,
        'resourceRequirements': resource_requirements
    }

    print('Generation: %d, Mix Create Next Generation Single Job')

    resp = batch_client.submit_job(
        jobName='mixcreatenextgen_%d' % (i_generation),
        jobQueue=job_queue,
        jobDefinition=batch_job_definition,
        containerOverrides=container_overrides,
        dependsOn=[{'jobId': prev_jobid}]
    )

    prev_jobid = resp['jobId']
