######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

import copy
from SALib.sample import saltelli
from SALib.analyze import sobol
import numpy as np
import pandas as pd

class SobolSensitivity:
    def __init__(self, init_array, feat_list, group_map=None):
        # Determine the bounds from the init array
        min_array = np.min(init_array, axis=0)
        max_array = np.max(init_array, axis=0)
        n_features = len(feat_list)
        self.parallel = False
        self.n_processors = 1  # cpu_count() - 1 # Leave 1 for the parent
        self.calc_conf = False # Calculate Confidence or Not
        self.num_resamples=10 #100
        print('Setting: n_processors = %d' % (self.n_processors))
        # Prevent getting bounds error
        # Can be sped up by removing the columns itself
        zero_bounds_idx = np.argwhere((max_array - min_array) == 0)
        max_array[zero_bounds_idx] += 0.0001

        bounds_list = [[min_array[i], max_array[i]] for i in np.arange(n_features)]

        self.problem = {
            'num_vars': n_features,
            'names': feat_list,
            'bounds': bounds_list
        }

        if(group_map is not None):
            group_list = [group_map[x] if x in group_map else 'Misc' for x in feat_list]
            self.problem['groups'] = group_list

    @staticmethod
    def create_group_map(csv_filename):
        group_map_pd = pd.read_csv(csv_filename, names=['var_name', 'group'])
        n_unique_var_names = len(group_map_pd['var_name'].unique())
        n_unique_groups = len(group_map_pd['group'].unique())

        group_map = {}
        for index, row in group_map_pd.iterrows():
            if row['group'] is np.nan:
                group_map[row['var_name']] = row['var_name']
            else:
                group_map[row['var_name']] = row['group']
        n_overall_groups = len(np.unique(list(group_map.values())))
        print('Total Vars: %d, Groups: %d, Dummy Groups: %d' % (n_unique_var_names, n_unique_groups, n_overall_groups))
        return group_map

    def generate_samples(self, n_samples=100):
        self.sample_array = saltelli.sample(self.problem, n_samples)
        return self.sample_array

    def generate_samples_partial(self, n_samples=100, n_partial=10, idx_partial=0):
        self.sample_array = saltelli.sample_partial(self.problem, Nss=n_samples, deltaNss=n_partial, idxNss=idx_partial)
        return self.sample_array


    def analyze_problem(self, eval_output):
        # analyze will determine the number of processors from the system call
        Si = sobol.analyze(self.problem, eval_output, calc_conf=self.calc_conf,
                           parallel=self.parallel, n_processors=self.n_processors, num_resamples=self.num_resamples)
        ut_matrix = copy.deepcopy(Si['S2'])
        ut_matrix = np.nan_to_num(ut_matrix)
        full_matrix = ut_matrix + ut_matrix.transpose() # Nothing is along the diagonal
        # Make negative elements due to sampling as zero
        full_matrix = np.abs(full_matrix)
        # full_matrix[full_matrix < 0] = 0.

        ret_dict = {
            'total_effect': Si['ST'].tolist(),
            'first_order': Si['S1'].tolist(),
            'second_order': full_matrix.tolist(), #Si['S2'].tolist(),
            'problem': self.problem,
        }
        if (self.calc_conf):
            loc_confidence = {
                'total_conf': Si['ST_conf'],
                'first_conf': Si['S1_conf'],
                'second_conf': Si['S2_conf']
            }
            ret_dict['confidence'] = loc_confidence

        return ret_dict


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    x1 = np.random.uniform(low=0.0, high=1.0, size=100)
    x2 = np.random.uniform(low=0.0, high=0.5, size=100)
    x_vector = np.vstack([x1, x2]).T


    def f(x):
        x1 = x[:, 0]
        x2 = x[:, 1]
        y = 5 * x1 + 4 * x2
        return y


    loc_ss = SobolSensitivity(x_vector, feat_list=['x1', 'x2'])
    n_samples = 100
    n_parts = 10
    delta_samples = int(n_samples/n_parts)

    fig, ax = plt.subplots(2, 1, figsize=(8, 8))
    x_eval = loc_ss.generate_samples(n_samples=100)
    ax[0].scatter(x_eval[:, 0], x_eval[:, 1])
    ax[0].set_title('Full Saltelli, with %d samples'%(n_samples))

    x_split_eval_list = []
    for i_split in np.arange(n_parts):

        x_split_eval = loc_ss.generate_samples_partial(n_samples=n_samples, n_partial=delta_samples, idx_partial=i_split*delta_samples)
        x_split_eval_list.append(x_split_eval)
        ax[1].scatter(x_split_eval[:, 0], x_split_eval[:, 1])
    ax[1].set_title('Incremental Saltelli, with %d samples x %d iter'%(delta_samples, n_parts))
    x_split_eval_3d = np.array(x_split_eval_list)
    x_split_eval_2d = np.vstack(x_split_eval_list)
    # Evaluate the error between full versus assembled parallel
    print('Max Error (full_eval - split_eval): %f'% (np.max(x_eval - x_split_eval_2d)))

    y_eval = f(x_eval)
    loc_dict = loc_ss.analyze_problem(y_eval)
