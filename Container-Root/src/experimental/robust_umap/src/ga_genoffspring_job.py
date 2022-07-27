# Give a generation and identifier as parent or offspring to trigger the batch run
import os
import boto3
import random
import json
import numpy as np
from dynamodb_json import json_util
from extract_dynamodb_records import extract_dynamodb_record
import GA.emo_mod as emo
from insert_dynamodb_records import extract_lb_ub, generate_candidate_workload_dict, \
    batch_upload_info_dict_to_dynamodbtable
from utils.hash_utils import generate_hash_str
from update_dynamodb_records import update_dynamodb_info

import inspyred
import random
from time import time
from GA.ec_mod import Bounder

if __name__ == "__main__":
    #from table_definition import table_name, ga_overview_table_name, ga_detail_table_name
    #from table_definition import n_char
    #from ga_definition import ga_run_specifier, n_population
    from ga_definition import candidate_fitness_extractor
    #from table_definition import region_name

    import configparser

    config = configparser.RawConfigParser()
    config.read('./template/config_template.conf')
    common_dict = config._sections['common']
    ga_dict = config._sections['GA']

    region_name = common_dict['region_name']
    table_name = ga_dict['table_name']
    ga_overview_table_name = ga_dict['ga_overview_table_name']
    ga_scenario_specifier = ga_dict['scenario_specifier']
    ga_detail_table_name = ga_dict[ 'ga_detail_table_name']
    n_char = int(ga_dict['n_char'])
    n_population = int(ga_dict['n_population'])

    with open('./template/workload_config_template.json', 'r') as fp:
        workload_config = json.load(fp)

    with open('./template/lhs_bounds_template.json', 'r') as fp:
        bounds_config = json.load(fp)

    session = boto3.session.Session()
    dynamodb = session.resource('dynamodb', region_name=region_name)

    population_str = 'population'  # Always read from parent and generate offspring

    generation_str = os.getenv('GENERATION') # Error out if it is not there
    generation_int = int(generation_str)

    print('Generation: %s, Population Str: %s'%(generation_str, population_str))
    # Lookup the value of the run_specifier from (population_str, generation_int)
    resp_dict = extract_dynamodb_record(ga_overview_table_name,
                                        run_specifier=ga_scenario_specifier,
                                        region_name=region_name,
                                        run_id=generation_int,
                                        dynamodb=dynamodb)

    run_specifier_str = resp_dict['info'][population_str]
    print('Run Specifier: %s'%(run_specifier_str))

    # Extract the data from the database
    # Loop through the population and extract the fitness values
    candidate_fit_resp_list = []
    for i_pop in np.arange(n_population):
        print('Extracting Population Fitness: %d'%(i_pop))
        try:
            resp_dict = extract_dynamodb_record(ga_detail_table_name,
                                                run_specifier=run_specifier_str,
                                                region_name=region_name,
                                                run_id=int(i_pop),
                                                dynamodb=dynamodb)
            resp_dict_converted = json_util.loads(resp_dict['info'])
            candidate_fit_resp_list.append(resp_dict_converted)
        except:
            print('Index: %d not found in dynamodb'%(i_pop))
            pass

    lb_ub_bounds = extract_lb_ub(bounds_config)
    if(generation_int == 0):
        # For first generation we need to extract and calculate fitness from the LHS sampling
        prev_gen_population, prev_gen_fitness = candidate_fitness_extractor(candidate_fit_resp_list, lookup_fitness=False)
    else:
        # For other generations, it will also be available in the database, just lookup
        prev_gen_population, prev_gen_fitness = candidate_fitness_extractor(candidate_fit_resp_list, lookup_fitness=True)

    prng = random.Random()
    prng.seed(time())

    ea = emo.NSGA2(prng)
    ea.variator = [inspyred.ec.variators.blend_crossover,
                   inspyred.ec.variators.gaussian_mutation]
    ea.terminator = inspyred.ec.terminators.generation_termination

    lb_ub_bounder = Bounder(lower_bound=lb_ub_bounds[0], upper_bound=lb_ub_bounds[1])
    ea.initialize(generator=None,  # kurasawe_generator,
                  evaluator=None,  # kurasawe_evaluator,
                  pop_size=n_population,
                  seeds=prev_gen_population,
                  maximize=False,
                  bounder=lb_ub_bounder,
                  max_generations=1,
                  seed_fitness=prev_gen_fitness,
                  integer_var_idx=[0, 1, 3])
    ea.generate_offsprings()
    ea.bound_offsprings()
    # Get the parents and save it in database for lookup
    # Convert this into a list for loading into database
    parents_list = []
    parent_fitness_list = []
    n_parents = len(ea.parents)
    n_offsprings = len(ea.offsprings)
    for index in np.arange(n_parents):
        candidate = ea.parents[index].candidate
        fitness = (ea.parents[index].fitness).values # Extract the list
        parents_list.append(candidate)
        parent_fitness_list.append(fitness)

    parent_ga_detail_dict_list = []
    for cur_val_list, cur_fitness in zip(parents_list, parent_fitness_list):
        loc_ga_detail_dict = {
            'candidate': cur_val_list,
            'fitness': cur_fitness
        }
        parent_ga_detail_dict_list.append(loc_ga_detail_dict)

    # Get the offsprings and trigger a batch
    offspring_candidates = ea.offsprings

    offspring_wl_dict_list = []
    offspring_ga_detail_dict_list = []
    for cur_val_list in offspring_candidates:
        loc_wl_dict = generate_candidate_workload_dict(cur_val_list, workload_config, bounds_config)
        loc_ga_detail_dict = {
            'candidate': cur_val_list
        }
        offspring_wl_dict_list.append(loc_wl_dict)
        offspring_ga_detail_dict_list.append(loc_ga_detail_dict)

    # Load up the ga_overview, detail and the workload tables
    parent_run_specifier_str = generate_hash_str(n_char=n_char)
    offspring_run_specifier_str = generate_hash_str(n_char=n_char)

    # Update the for the offspring
    update_expression = 'set info.parent=:parent, info.offspring=:offspring'
    expression_attribute_values = {
        ':parent': parent_run_specifier_str,
        ':offspring': offspring_run_specifier_str
    }
    print(update_expression)
    print(expression_attribute_values)

    update_dynamodb_info(name=ga_overview_table_name,
                         hash_str=ga_scenario_specifier,
                         id=generation_int,
                         update_expression=update_expression,
                         expression_attribute_values=expression_attribute_values,
                         dynamodb=dynamodb,
                         region_name=region_name)

    # Batch upload the dict to a dynamo table
    batch_upload_info_dict_to_dynamodbtable(name=ga_detail_table_name,
                                            run_specifier=offspring_run_specifier_str,
                                            run_id_list=list(np.arange(n_offsprings)),
                                            info_dict_list=offspring_ga_detail_dict_list,
                                            dynamodb=dynamodb,
                                            region_name=region_name)
    batch_upload_info_dict_to_dynamodbtable(name=table_name,
                                            run_specifier=offspring_run_specifier_str,
                                            run_id_list=list(np.arange(n_offsprings)),
                                            info_dict_list=offspring_wl_dict_list,
                                            dynamodb=dynamodb,
                                            region_name=region_name)
    # Batch upload parent only in the ga_detail table
    batch_upload_info_dict_to_dynamodbtable(name=ga_detail_table_name,
                                            run_specifier=parent_run_specifier_str,
                                            run_id_list=list(np.arange(n_parents)),
                                            info_dict_list=parent_ga_detail_dict_list,
                                            dynamodb=dynamodb,
                                            region_name=region_name)

