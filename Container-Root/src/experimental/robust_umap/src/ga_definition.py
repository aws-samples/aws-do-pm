import numpy as np
import GA.emo_mod as emo

def candidate_fitness_extractor(batch_evaluate_dict_list, lookup_fitness=False):
    candidates = []
    fitness = []
    for cur_dict in batch_evaluate_dict_list:
        candidates.append(cur_dict['candidate'])
        if(lookup_fitness):
            # Just lookup the value of fitness array
            # Convert it into a Pareto Object
            fitness.append(emo.Pareto(cur_dict['fitness']))
        else:
            # Calculate the fitness from the raw outputs from workload
            try:
                f1 = cur_dict['entropy_train']
                f2 = cur_dict['entropy_test']
                f3 = cur_dict['n_clusters_train']
                f4 = np.abs(f1 - f2)
                #fitness.append(emo.Pareto([f1, f2, f3, f4]))
                fitness.append(emo.Pareto([f1, f3, f4]))
            except:
                print('Penalizing: Cluster Run Failed')
                fitness.append(emo.Pareto([.5, 50, .5]))
    return candidates, fitness
