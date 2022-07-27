# Give a generation and identifier as parent or offspring to trigger the batch run
import os
import boto3
import random
import json
import numpy as np
from dynamodb_json import json_util
from mnist_clusterer import clusterer_main
from extract_dynamodb_records import extract_dynamodb_record

if __name__ == "__main__":
    #from table_definition import ga_overview_table_name
    #from ga_definition import ga_run_specifier, n_population
    #from table_definition import region_name

    import configparser

    config = configparser.RawConfigParser()
    config.read('./template/config_template.conf')
    common_dict = config._sections['common']
    ga_dict = config._sections['GA']

    region_name = common_dict['region_name']
    table_name = ga_dict['table_name']
    ga_overview_table_name = ga_dict['ga_overview_table_name']
    scenario_specifier = ga_dict['scenario_specifier']

    session = boto3.session.Session()
    dynamodb = session.resource('dynamodb', region_name=region_name)

    population_str = os.getenv('POPULATION') # population or parent or offspring

    generation_str = os.getenv('GENERATION')
    generation_int = int(generation_str)
    batch_job_array_index = os.getenv('AWS_BATCH_JOB_ARRAY_INDEX')

    print('Generation: %s, Population: %s, Batch Job Array Index: %s'%(generation_str, population_str, batch_job_array_index))

    # Lookup the value of the run_specifier from (population_str, generation_int)
    try:
        resp_dict = extract_dynamodb_record(ga_overview_table_name,
                                            run_specifier=scenario_specifier,
                                            region_name=region_name,
                                            run_id=generation_int,
                                            dynamodb=dynamodb)
        run_specifier_str = resp_dict['info'][population_str]
        print('Run Specifier: %s'%(run_specifier_str))
        clusterer_main(run_specifier=run_specifier_str,
                       batch_job_array_index=batch_job_array_index)
    except:
        print('Exception in dynamodb record, due to offspring not matching count')
        pass
