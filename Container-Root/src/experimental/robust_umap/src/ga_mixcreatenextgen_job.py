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
    upload_info_dict_to_dynamodbtable, batch_upload_info_dict_to_dynamodbtable
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

    generation_str = os.getenv('GENERATION')
    generation_int = int(generation_str)
    print('Generation: %s'%(generation_str))

    # Lookup the value of the run_specifier from (population_str, generation_int)
    resp_dict = extract_dynamodb_record(ga_overview_table_name,
                                        run_specifier=ga_scenario_specifier,
                                        region_name=region_name,
                                        run_id=generation_int,
                                        dynamodb=dynamodb)

    population_run_specifier_str = resp_dict['info']['population']
    parent_run_specifier_str = resp_dict['info']['parent']
    offspring_run_specifier_str = resp_dict['info']['offspring']

    # Extract the data from the database
    lb_ub_bounds = extract_lb_ub(bounds_config)
    # Loop through the population and extract the fitness values
    candidate_fit_resp_list = []
    for i_pop in np.arange(n_population):
        print('Extracting Population Fitness: %d'%(i_pop))
        try:
            resp_dict = extract_dynamodb_record(ga_detail_table_name,
                                                run_specifier=population_run_specifier_str,
                                                region_name=region_name,
                                                run_id=int(i_pop),
                                                dynamodb=dynamodb)
            resp_dict_converted = json_util.loads(resp_dict['info'])
            candidate_fit_resp_list.append(resp_dict_converted)
        except:
            print('Index: %d not found in dynamodb'%(i_pop))
            pass
    if (generation_int == 0):
        population, population_fitness = candidate_fitness_extractor(candidate_fit_resp_list, lookup_fitness=False)
    else:
        population, population_fitness = candidate_fitness_extractor(candidate_fit_resp_list, lookup_fitness=True)

    # Loop through the parents and extract the fitness values
    candidate_fit_resp_list = []
    for i_pop in np.arange(n_population):
        print('Extracting Parent Fitness: %d'%(i_pop))
        try:
            resp_dict = extract_dynamodb_record(ga_detail_table_name,
                                                run_specifier=parent_run_specifier_str,
                                                region_name=region_name,
                                                run_id=int(i_pop),
                                                dynamodb=dynamodb)
            resp_dict_converted = json_util.loads(resp_dict['info'])
            candidate_fit_resp_list.append(resp_dict_converted)
        except:
            print('Index: %d not found in dynamodb'%(i_pop))
            pass
    parents, parent_fitness = candidate_fitness_extractor(candidate_fit_resp_list, lookup_fitness=True)

    # Loop and extract the offsprings and its fitness
    candidate_fit_resp_list = []
    for i_pop in np.arange(n_population):
        print('Extracting Offspring Fitness: %d'%(i_pop))
        try:
            resp_dict = extract_dynamodb_record(ga_detail_table_name,
                                                run_specifier=offspring_run_specifier_str,
                                                region_name=region_name,
                                                run_id=int(i_pop),
                                                dynamodb=dynamodb)
            resp_dict_converted = json_util.loads(resp_dict['info'])
            candidate_fit_resp_list.append(resp_dict_converted)
        except:
            print('Index: %d not found in dynamodb'%(i_pop))
            pass

    offsprings, offspring_fitness = candidate_fitness_extractor(candidate_fit_resp_list, lookup_fitness=False)


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
                  seeds=population,
                  maximize=False,
                  bounder=lb_ub_bounder,
                  max_generations=1,
                  seed_fitness=population_fitness,
                  integer_var_idx=[0, 1, 3],
                  parents=parents,
                  parent_fitness=parent_fitness,
                  offsprings=offsprings,
                  offspring_fitness=offspring_fitness)

    ea.create_next_generation()
    # Get the offsprings and trigger a batch
    #next_gen_candidates = ea.population

    # Convert this into a list for loading into database
    next_gen_population_list = []
    next_gen_fitness_list = []
    for index in np.arange(n_population):
        try:
            candidate = ea.population[index].candidate
            fitness = (ea.population[index].fitness).values
            next_gen_population_list.append(candidate)
            next_gen_fitness_list.append(fitness)
        except:
            print('Skipping: %d in loading table for next generation'%(index))
            pass

    nextgen_ga_detail_dict_list = []
    for next_gen_pop, next_gen_fit in zip(next_gen_population_list, next_gen_fitness_list):
        loc_ga_detail_dict = {
            'candidate': next_gen_pop,
            'fitness': next_gen_fit
        }
        nextgen_ga_detail_dict_list.append(loc_ga_detail_dict)

    # Create a new identifier to load in the overview table (as Mixed State)
    # Load up the ga_overview, detail and the workload tables
    run_specifier_str = generate_hash_str(n_char=n_char)

    # Update the for the offspring
    update_expression = 'set info.mixnextgen=:mixnextgen'
    expression_attribute_values = {
        ':mixnextgen': run_specifier_str
    }

    update_dynamodb_info(name=ga_overview_table_name,
                         hash_str=ga_scenario_specifier,
                         id=generation_int,
                         update_expression=update_expression,
                         expression_attribute_values=expression_attribute_values,
                         dynamodb=dynamodb,
                         region_name=region_name)

    # Batch upload the dict to a dynamo table
    batch_upload_info_dict_to_dynamodbtable(name=ga_detail_table_name,
                                            run_specifier=run_specifier_str,
                                            run_id_list=list(np.arange(n_population)),
                                            info_dict_list=nextgen_ga_detail_dict_list,
                                            dynamodb=dynamodb,
                                            region_name=region_name)

    # Enter this in the overview table as parent
    # Create a new record
    info_dict = {
        'population': run_specifier_str
    }
    upload_info_dict_to_dynamodbtable(name=ga_overview_table_name,
                                      run_specifier=ga_scenario_specifier,
                                      run_id=generation_int+1,
                                      info_dict=info_dict,
                                      dynamodb=dynamodb,
                                      region_name=region_name)
