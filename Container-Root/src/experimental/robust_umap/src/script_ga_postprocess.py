import boto3
from tqdm import tqdm
import numpy as np
from dynamodb_json import json_util
from extract_dynamodb_records import extract_dynamodb_record
import dill
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 unused import
import pandas as pd
import json
import seaborn as sns
from boto3.dynamodb.conditions import Key
import pareto

def query_table(dynamodb, table_name, key=None, value=None):
    table = dynamodb.Table(table_name)

    if key is not None and value is not None:
        filtering_exp = Key(key).eq(value)
        return table.query(KeyConditionExpression=filtering_exp)

    raise ValueError('Parameters missing or invalid')


def is_pareto_efficient_simple(costs):
    """
    Find the pareto-efficient points
    :param costs: An (n_points, n_costs) array
    :return: A (n_points, ) boolean array, indicating whether each point is Pareto efficient
    """
    is_efficient = np.ones(costs.shape[0], dtype=bool)
    # Suppress the nan error messages that can come with outlier groupings
    with np.errstate(invalid='ignore'):
        for i, c in enumerate(costs):
            if is_efficient[i]:
                is_efficient[is_efficient] = np.any(costs[is_efficient] < c, axis=1)  # Keep any point with a lower cost
                is_efficient[i] = True  # And keep self
    return is_efficient


def identify_pareto(scores, population_ids):
    """
    Identifies a single Pareto front, and returns the population IDs of
    the selected solutions.
    """
    population_size = scores.shape[0]
    # Create a starting list of items on the Pareto front
    # All items start off as being labelled as on the Parteo front
    pareto_front = np.ones(population_size, dtype=bool)
    # Loop through each item. This will then be compared with all other items
    for i in range(population_size):
        # Loop through all other items
        for j in range(population_size):
            # Check if our 'i' pint is dominated by out 'j' point
            if all(scores[j] <= scores[i]) and any(scores[j] < scores[i]):
                # j dominates i. Label 'i' point as not on Pareto front
                pareto_front[i] = 0
                # Stop further comparisons with 'i' (no more comparisons needed)
                break
    # Return ids of scenarios on pareto front
    return population_ids[pareto_front]


if __name__ == "__main__":
    # from table_definition import table_name, ga_overview_table_name, ga_detail_table_name
    # from ga_definition import ga_run_specifier, n_generation, n_population
    from ga_definition import candidate_fitness_extractor
    # from table_definition import region_name
    import os

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
    n_generation = int(ga_dict['n_generation'])
    n_population = int(ga_dict['n_population'])

    if not os.path.exists('plots'):
        os.mkdir('plots')
    if not os.path.exists('plots/' + ga_scenario_specifier):
        os.mkdir('plots/' + ga_scenario_specifier)
    plt_dir = 'plots/' + ga_scenario_specifier

    dill_file = plt_dir + '/' + 'candidate_fitness_3d.dill'
    get_data = True

    ent_threshold = 0.15
    n_generation = 19
    if get_data:
        session = boto3.session.Session()
        dynamodb = session.resource('dynamodb', region_name=region_name)
        population_str = 'offspring'  # 'population' only for lookup
        lookup_fitness = False

        candidate_2d_list = []
        fitness_2d_list = []
        all_run_specifier = []
        # n_generation = 16
        for i_generation in tqdm(np.arange(0, n_generation)):
            print('Extracting: Generation %d/%d' % (i_generation, n_generation))
            # Lookup the value of the run_specifier from (population_str, generation_int)
            resp_dict = extract_dynamodb_record(ga_overview_table_name,
                                                run_specifier=ga_scenario_specifier,
                                                region_name=region_name,
                                                run_id=int(i_generation),
                                                dynamodb=dynamodb)

            run_specifier_str = resp_dict['info'][population_str]

            # Pull the data from the database
            # Loop through the population and extract the fitness values
            resp_dict = query_table(dynamodb, ga_detail_table_name, 'run_specifier', run_specifier_str)
            eval_dict_converted = [json_util.loads(cur_item['info']) for cur_item in resp_dict['Items']]
            candidate_1d_list, fitness_po_list = candidate_fitness_extractor(eval_dict_converted,
                                                                             lookup_fitness=lookup_fitness)
            if lookup_fitness:
                fitness_1d_list = fitness_po_list
            else:
                # Convert from pareto object
                fitness_1d_list = [x.values for x in fitness_po_list]

            candidate_2d_list.append(candidate_1d_list)
            fitness_2d_list.append(fitness_1d_list)
            all_run_specifier.append(run_specifier_str)

        fitness_3d_array = np.array(fitness_2d_list)
        fitness_3d_array[:, :, 0] = fitness_3d_array[:, :, 0] / np.log(2)
        fitness_3d_array[:, :, 2] = fitness_3d_array[:, :, 2] / np.log(2)

        # fitness_3d_array[fitness_3d_array[:,:,0]>0.5] = np.nan
        # fitness_3d_array[fitness_3d_array[:,:,1]>20] = np.nan
        # fitness_3d_array[fitness_3d_array[:,:,2]>0.5] = np.nan

        candidates_3d_array = np.array(candidate_2d_list)

        file = open(dill_file, 'wb')
        # dump information to that file
        dill.dump([fitness_3d_array, candidates_3d_array, all_run_specifier], file)
        # close the file
        file.close()

        n_gen, n_pop, n_fit = fitness_3d_array.shape
        pareto_gen = n_gen - 1

        print('Pareto run specifier: %s' % (all_run_specifier[pareto_gen]))
        last_generation_results = fitness_3d_array[pareto_gen, :, :]
    else:
        print('Loading data from dill file')
        file = open(dill_file, 'rb')
        fitness_3d_array, candidates_3d_array, all_run_specifier = dill.load(file)
        file.close()

        n_gen, n_pop, n_fit = fitness_3d_array.shape
        pareto_gen = n_gen - 1

    # %% Find Pareto
    population_scores = fitness_3d_array.reshape(n_gen * n_pop, n_fit)
    population_ids = np.arange(population_scores.shape[0])
    n_gen, n_pop, n_var = candidates_3d_array.shape
    population_params = candidates_3d_array.reshape(n_gen * n_pop, n_var)
    pareto_idx = identify_pareto(population_scores, population_ids)
    pareto_candidates = population_params[pareto_idx]
    pareto_values = population_scores[pareto_idx]

    # Dump all the population scores into a csv file
    all_pop_pd_list = []
    for i_gen in np.arange(n_gen):
        add_pd = pd.DataFrame()
        add_pd['entropy_train'] = fitness_3d_array[i_gen, :, 0]
        add_pd['n_clusters'] = fitness_3d_array[i_gen, :, 1]
        add_pd['entropy_diff'] = fitness_3d_array[i_gen, :, 2]
        add_pd['generation'] = i_gen
        all_pop_pd_list.append(add_pd)
    all_pop_pd = pd.concat(all_pop_pd_list)
    all_pop_pd.to_csv(plt_dir + '/' + 'all_pop_export.csv')

    # Extract Pareto through another scheme (per Arun)
    nds_values = pareto.eps_sort(population_scores.tolist(), [0, 1, 2])

    print('Pareto Length: %d Vs %d'%(len(pareto_values), len(nds_values)))
    print('Checking 1:1 Match, Report Mismatches')
    # Checking if there is a match
    for cur_nds in tqdm(nds_values):
        match_found = np.sum(np.sum(np.abs(pareto_values - np.array(cur_nds)), axis=1) <= 1E-6)
        if match_found != 1:
            print(cur_nds)

    idx = np.intersect1d(np.argwhere(pareto_values[:, 0] < 1.0), np.argwhere(pareto_values[:, 1] > 0))
    sel_idx = pareto_idx[idx]
    sel_candidates = population_params[sel_idx]
    sel_candidate_fitness = population_scores[sel_idx]
    pop_gen = []
    pop_gen_idx = []
    sel_candidates_specifier = []
    for val in sel_idx:
        gen, gen_idx = np.divmod(val, n_pop)
        pop_gen.append(gen)
        pop_gen_idx.append(gen_idx)
        sel_candidates_specifier.append(all_run_specifier[gen])

    data_dict = dict()
    data_dict['run_specifier'] = sel_candidates_specifier
    data_dict['generation'] = pop_gen
    data_dict['generation_index'] = pop_gen_idx
    data_dict['num_neighbors'] = list(sel_candidates[:, 0])
    data_dict['num_components'] = list(sel_candidates[:, 1])
    data_dict['min_dist'] = list(sel_candidates[:, 2])
    data_dict['min_samples'] = list(sel_candidates[:, 3])
    data_dict['eps'] = list(sel_candidates[:, 4])
    data_dict['train_entropy'] = list(sel_candidate_fitness[:, 0])
    data_dict['num_cluster'] = list(sel_candidate_fitness[:, 1])
    data_dict['entropy_diff'] = list(sel_candidate_fitness[:, 2])

    sel_cand_df = pd.DataFrame.from_dict(data_dict)
    sel_cand_df.to_csv(plt_dir + '/' + 'pareto_candidates.csv')

    # %%

    fig = plt.figure(figsize=(12, 12))
    ax = Axes3D(fig)
    # ax = fig.add_subplot(111, projection='3d')
    ax.scatter(fitness_3d_array[:, :, 1], fitness_3d_array[:, :, 0], fitness_3d_array[:, :, 2], color='blue',
               alpha=0.3, s=30)
    ax.scatter(sel_candidate_fitness[:, 1], sel_candidate_fitness[:, 0], sel_candidate_fitness[:, 2], color='red', s=80)
    ax.set_ylabel('Train Entropy', fontsize=16, fontweight='bold')
    ax.set_xlabel('Number of Clusters', fontsize=16, fontweight='bold')
    ax.set_zlabel('Abs Entropy Diff.', fontsize=16, fontweight='bold')
    # ax.set_xlim3d([1, 0])
    # ax.set_ylim3d([np.max(fitness_3d_array[:, :, 1]) + 5, 0])
    # ax.view_init(azim=-165, elev=15)
    ax.legend(['Population', 'Pareto'])
    plt.title('GA Optimization (%d Generations)' % (n_gen), fontsize=18, fontweight='bold')
    plt.savefig(plt_dir + '/' + 'FitnessPlot_3D.png')

    plt.figure(figsize=(10, 10))
    p = 0.01 * np.arange(1, 100)
    p_ent = -(p * np.log2(p) + (1 - p) * np.log2(1 - p))
    plt.plot(p, p_ent, 'b.', ms=6, mew=4)
    plt.grid()
    plt.xlabel('Probability', fontsize=16, fontweight='bold')
    plt.ylabel('Entropy', fontsize=16, fontweight='bold')
    plt.xticks(np.arange(0, 101, 5) * 0.01)
    plt.yticks(np.arange(0, 101, 5) * 0.01)
    plt.title('Entropy Vs Probability', fontsize=18, fontweight='bold')
    plt.savefig(plt_dir + '/' + 'EntropyVsProbability.png')

    plt.figure(figsize=(10, 10))
    ax1 = plt.subplot(2, 1, 1)
    ax1.plot(fitness_3d_array[:, :, 1], fitness_3d_array[:, :, 0], 'b.', ms=4, mew=4)
    ax1.plot(sel_candidate_fitness[:, 1], sel_candidate_fitness[:, 0], 'r.', ms=8, mew=6)
    plt.xlabel('Number of Clusters', fontsize=16, fontweight='bold')
    plt.ylabel('Train Entropy', fontsize=16, fontweight='bold')
    plt.yticks(np.arange(0, 101, 5) * 0.01)
    plt.xlim(0, 12)
    plt.grid()
    ax2 = plt.subplot(2, 1, 2, sharex=ax1)
    ax2.plot(fitness_3d_array[:, :, 1], fitness_3d_array[:, :, 2], 'b.', ms=4, mew=4)
    ax2.plot(sel_candidate_fitness[:, 1], sel_candidate_fitness[:, 2], 'r.', ms=8, mew=6)
    plt.xlabel('Number of Clusters', fontsize=16, fontweight='bold')
    plt.ylabel('Abs. Entropy Diff.', fontsize=16, fontweight='bold')
    plt.xlim(0, 12)
    plt.yticks(np.arange(0, 101, 5) * 0.001)
    plt.grid()
    plt.savefig(plt_dir + '/' + 'Pareto_2D_%s.png' % (str(pareto_gen)))

    # %%

    fig = plt.figure(figsize=(12, 12))
    ax = Axes3D(fig)
    ax.scatter(sel_candidate_fitness[:, 1], sel_candidate_fitness[:, 0], sel_candidate_fitness[:, 2], color='red', s=80)
    ax.set_ylabel('Train Entropy', fontsize=16, fontweight='bold')
    ax.set_xlabel('Number of Clusters', fontsize=16, fontweight='bold')
    ax.set_zlabel('Abs. Entropy Diff.', fontsize=16, fontweight='bold')
    # ax.set_xlim3d([1, 0])
    # ax.set_ylim3d([np.max(fitness_3d_array[:, :, 1]) + 5, 0])
    # ax.view_init(azim=-165, elev=15)
    ax.legend(['Pareto'])
    plt.title('GA Optimization (%d Generations)' % (n_gen), fontsize=18, fontweight='bold')
    plt.savefig(plt_dir + '/' + 'FitnessPlot_3D_Pareto%s.png' % (str(pareto_gen)))

    # %%
    plt.figure(figsize=(10, 6))
    plt.plot(fitness_3d_array[:, :, 1], fitness_3d_array[:, :, 0], 'b.', ms=4, mew=4)
    plt.plot(sel_candidate_fitness[:, 1], sel_candidate_fitness[:, 0], 'r.', ms=8, mew=8)
    plt.xlabel('Number of Clusters', fontsize=16, fontweight='bold')
    plt.ylabel('Train Entropy', fontsize=16, fontweight='bold')
    plt.xlim(0, 12)
    plt.grid()
    plt.savefig(plt_dir + '/' + 'TrainEntropyVsCluster.png')

    plt.figure(figsize=(10, 6))
    plt.plot(fitness_3d_array[:, :, 1], fitness_3d_array[:, :, 2], 'b.', ms=4, mew=4)
    plt.plot(sel_candidate_fitness[:, 1], sel_candidate_fitness[:, 2], 'r.', ms=8, mew=8)
    plt.xlabel('Number of Clusters', fontsize=16, fontweight='bold')
    plt.ylabel('Abs. Entropy Diff.', fontsize=16, fontweight='bold')
    plt.xlim(0, 12)
    plt.grid()
    plt.savefig(plt_dir + '/' + 'EntropyDiffVsCluster.png')

    # %%
    avg_fitness = np.mean(fitness_3d_array, axis=1)

    plt.figure(figsize=(10, 10))
    plt.subplot(311)
    plt.plot(avg_fitness[:, 0], 'b', marker='o', ms=4, mew=4)
    # plt.xlabel('Generation', fontsize=16, fontweight='bold')
    plt.ylabel('Avg. Train Entropy', fontsize=16, fontweight='bold')
    plt.grid()
    plt.subplot(312)
    plt.plot(np.round(avg_fitness[:, 1]), 'b', marker='o', ms=4, mew=4)
    # plt.xlabel('Generation', fontsize=16, fontweight='bold')
    plt.ylabel('Avg. Clusters', fontsize=16, fontweight='bold')
    plt.grid()
    plt.subplot(313)
    plt.plot(avg_fitness[:, 2], 'b', marker='o', ms=4, mew=4)
    plt.xlabel('Generation', fontsize=16, fontweight='bold')
    plt.ylabel('Avg. Entropy Diff', fontsize=16, fontweight='bold')
    plt.grid()
    plt.suptitle('Fitness Vs Generation', fontsize=16, fontweight='bold')
    plt.savefig(plt_dir + '/' + 'FitnessConvergence.png')

    # %%
    n_gen, n_pop, n_fit = fitness_3d_array.shape
    fitness_var_list = ['Train Entropy', 'N Clusters', 'Absolute Delta Entropy']
    for idx_fit, cur_var in enumerate(fitness_var_list):
        select_fitness_2d = fitness_3d_array[:, :, idx_fit]
        pd_list = []
        for i_gen in np.arange(n_gen):
            add_pd = pd.DataFrame()
            add_pd[cur_var] = select_fitness_2d[i_gen, :]
            add_pd['Generation'] = i_gen
            pd_list.append(add_pd)
        overall_pd = pd.concat(pd_list)
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        sns.swarmplot(x='Generation', y=cur_var, data=overall_pd, ax=ax)
        plt.title('%s vs Generation' % (cur_var), fontsize=18, fontweight='bold')
        ax.set_ylabel(cur_var, fontsize=16, fontweight='bold')
        ax.set_xlabel('Generation', fontsize=16, fontweight='bold')
        plt.grid()
        plt.savefig(plt_dir + '/' + 'FitnessVsGen_var%d.png' % (idx_fit))
