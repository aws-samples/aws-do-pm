import configparser
import gzip
import dill
import h5py
import numpy as np
import os
import pandas as pd
import subprocess
# import umap
import cudf, cuml
from cuml.manifold import UMAP
from cuml import DBSCAN as cumlDBSCAN

from decimal import Decimal
from dynamodb_json import json_util
from extract_dynamodb_records import extract_dynamodb_record
from functools import partial
from multiprocessing import Pool
from scipy import stats
from sklearn.model_selection import train_test_split
from update_dynamodb_records import update_dynamodb_info
from utils.timeit import timeit
from utils.vec_matrix import convert_cluster_vec_to_im


def cluster_data(config, train_data, test_data, job_num):
    print("ID of process: {}".format(os.getpid()))

    umap_data = train_data

    embedding_func = UMAP(
        n_neighbors=config['embedding_params']['n_neighbors'],
        n_components=config['embedding_params']['n_components'],
        # random_state=np.random.RandomState(loc_random_state_embedding),  # random_state_embedding,
        # low_memory=False,
        init='random',  # embedding_params['init'],  # spectral default has issues
        min_dist=config['embedding_params']['min_dist'],
        # metric=config['embedding_params']['metric'],
        n_epochs=config['embedding_params']['n_epochs']).fit(umap_data)

    embedding_train = embedding_func.transform(train_data)
    embedding_test = embedding_func.transform(test_data)

    hdbscan_train = embedding_train
    cuml_dbscan = cuml.DBSCAN(
        eps=config['cluster_params']['eps'],
        min_samples=config['cluster_params']['min_samples'])

    cluster_func = cuml_dbscan.fit(hdbscan_train)
    cluster_train = cluster_func.fit_predict(embedding_train)
    cluster_test = cluster_func.fit_predict(embedding_test)

    # train_membership_vector = hdbscan.membership_vector(cluster_func, embedding_train)
    # train_cluster_strength = np.sum(train_membership_vector, axis=1)
    # cluster_train = np.argmax(train_membership_vector, axis=1)

    # self.cluster_test, test_strengths = hdbscan.approximate_predict(
    #    cluster_func, self.embedding_test)
    # test_membership_vector = hdbscan.membership_vector(cluster_func, embedding_test)
    # test_cluster_strength = np.sum(test_membership_vector, axis=1)
    # cluster_test = np.argmax(test_membership_vector, axis=1)

    results = dict()
    results['embedding_train'] = embedding_train
    # results['train_membership_vector'] = train_membership_vector
    results['cluster_train'] = cluster_train
    # results['train_cluster_strength'] = train_cluster_strength
    results['embedding_test'] = embedding_test
    # results['test_membership_vector'] = test_membership_vector
    results['cluster_test'] = cluster_test
    # results['test_cluster_strength'] = test_cluster_strength

    return results


class mnist_clusterer:
    def __init__(self,
                 bucket_name,
                 region_name):
        self.bucket_name = bucket_name
        self.region_name = region_name

    @timeit
    def _load_data(self, data_folder_prefix, train_fname, test_fname):

        s3_data_folder = 's3://%s/%s' % (self.bucket_name,
                                         data_folder_prefix)
        cur_data_folder = os.getcwd()
        print('Current Data Folder: %s'%(cur_data_folder))
        s3_sync_cli_cmd = ['aws', 's3', 'sync', s3_data_folder, cur_data_folder]
        subprocess.run(s3_sync_cli_cmd, check=True, timeout=120)
        print('Extracting Data from Numpy Gzip Files')

        with gzip.open('%s/%s'%(cur_data_folder, train_fname), 'rb') as imgpath:
            train_array_2d = np.frombuffer(imgpath.read(), dtype=np.uint8,
                                           offset=16).reshape(-1, 784)
            train_array_2d = train_array_2d * 1.0/255.0

        with gzip.open('%s/%s'%(cur_data_folder, test_fname), 'rb') as imgpath:
            test_array_2d = np.frombuffer(imgpath.read(), dtype=np.uint8,
                                          offset=16).reshape(-1, 784)
            test_array_2d = test_array_2d * 1.0/255.0

        return train_array_2d[0:15000,:], test_array_2d[0:5000,:]
        # return train_array_2d, test_array_2d

    # Post process to calculate entropy from multiple runs
    @timeit
    def calculate_cluster_switch_metrics(self, train_array_2d, test_array_2d,
                                         embedding_params, cluster_params, robustness_params, **kwargs):
        output_prefix = 'output'
        success_run_idx_list = []

        config = dict()
        config['embedding_params'] = embedding_params.copy()
        config['cluster_params'] = cluster_params.copy()
        n_repeats = robustness_params['n_repeats']
        # config['embedding_params']['n_neighbors'] = n_neighbors
        # config['embedding_params']['n_components'] = n_components
        # config['embedding_params']['min_dist'] = min_dist
        # config['embedding_params']['metric'] = metric
        # config['embedding_params']['n_epochs'] = n_epochs
        #
        # config['cluster_params']['min_samples'] = min_samples
        # config['cluster_params']['min_cluster_size'] = min_cluster_size

        cluster_partial_func = partial(cluster_data, config, train_array_2d, test_array_2d)
        # p = Pool(processes=4)
        # jobs_ = list(np.arange(n_repeats))
        # print()
        # accumulate_results = p.map(cluster_partial_func, jobs_)
        # p.close()
        # p.join()
        accumulate_results = []
        for i_job in np.arange(n_repeats):
            loc_result = cluster_partial_func(i_job)
            accumulate_results.append(loc_result)

        for i_sub_run_id in np.arange(n_repeats):
            print('Run: %d/%d' % (i_sub_run_id, n_repeats))
            try:
                output_filename = '%s_%d.h5' % (output_prefix, i_sub_run_id)
                if (not os.path.exists(output_filename)):
                    results = accumulate_results[i_sub_run_id]
                    # Export h5 file of selected data for cross platform compatibility
                    with h5py.File(output_filename, 'w') as export_h5:

                        # Embedding
                        export_h5.create_dataset('train_embedding', data=results['embedding_train'])
                        export_h5.create_dataset('test_embedding', data=results['embedding_test'])

                        # Cluster Assignment
                        export_h5.create_dataset('train_cluster', data=results['cluster_train'])
                        export_h5.create_dataset('test_cluster', data=results['cluster_test'])

                        # # Cluster Membership
                        # export_h5.create_dataset('train_membership_vector', data=results['train_membership_vector'])
                        # export_h5.create_dataset('test_membership_vector', data=results['test_membership_vector'])
                        #
                        # # Cluster Strength Prediction
                        # export_h5.create_dataset('train_cluster_strength', data=results['train_cluster_strength'])
                        # export_h5.create_dataset('test_cluster_strength', data=results['test_cluster_strength'])

                    print('Exported h5: %s' % (output_filename))
                    success_run_idx_list.append(i_sub_run_id)
                else:
                    print('Using Output: %d on Local Disk' % (i_sub_run_id))
                    success_run_idx_list.append(i_sub_run_id)
            except:
                print('Exception encountered, Skipping: %d' % (i_sub_run_id))
                pass
        # End of Parallel implementation of UMAP + HDBSCAN

        n_success_runs = len(success_run_idx_list)
        print('Num Successful Runs for Probability Calculation: %d' % (n_success_runs))
        # All the outputs are present locally
        # Accumulate the matrix in a sparse way to be scalable w.r.t. memory
        # Initialize a sparse matrix
        n_train, _ = train_array_2d.shape
        n_test, _ = test_array_2d.shape

        train_im_array_2d = np.zeros((n_train, n_train), dtype=np.int8)
        test_im_array_2d = np.zeros((n_test, n_test), dtype=np.int8)
        n_clusters_train_agg = []
        n_clusters_test_agg = []
        for i_sub_run_id in success_run_idx_list:
            print('Entropy Calculation: %d/%d' % (i_sub_run_id, n_repeats))
            h5_fp = h5py.File('%s_%d.h5' % (output_prefix, i_sub_run_id), 'r')
            outdict = {}
            for key in h5_fp.keys():
                outdict[key] = h5_fp.get(key)[()]  # h5_fp.get(key).value  # h5_fp[key]

            loc_im_2d = convert_cluster_vec_to_im(outdict['train_cluster'])
            train_im_array_2d += loc_im_2d
            loc_im_2d = convert_cluster_vec_to_im(outdict['test_cluster'])
            test_im_array_2d += loc_im_2d

            n_train_clusters = len(np.unique(outdict['train_cluster']))
            n_test_clusters = len(np.unique(outdict['test_cluster']))
            n_clusters_train_agg.append(n_train_clusters)
            n_clusters_test_agg.append(n_test_clusters)

        eps = np.finfo(float).eps
        p_train_im_array_2d = train_im_array_2d / n_success_runs
        p_test_im_array_2d = test_im_array_2d / n_success_runs

        train_entropy_1d = p_train_im_array_2d * np.log(p_train_im_array_2d + eps) + \
                           (1 - p_train_im_array_2d) * np.log(1 - p_train_im_array_2d + eps)
        test_entropy_1d = p_test_im_array_2d * np.log(p_test_im_array_2d + eps) + \
                          (1 - p_test_im_array_2d) * np.log(1 - p_test_im_array_2d + eps)

        train_entropy_avg = -np.average(train_entropy_1d)
        test_entropy_avg = -np.average(test_entropy_1d)

        print('Train Cluster Count' + str(n_clusters_train_agg))
        print('Test Cluster Count' + str(n_clusters_test_agg))
        print('Train Entropy: %f' % (train_entropy_avg))
        print('Test Entropy: %f' % (test_entropy_avg))

        update_expression = 'set info.n_clusters_train=:nctrain, info.n_clusters_test=:nctest, info.entropy_train=:etrain, info.entropy_test=:etest'
        expression_attribute_values = {
            ':nctrain': Decimal(str(stats.mode(n_clusters_train_agg)[0][0])),
            ':nctest': Decimal(str(stats.mode(n_clusters_test_agg)[0][0])),
            ':etrain': Decimal(str(train_entropy_avg)),
            ':etest': Decimal(str(test_entropy_avg))
        }

        return update_expression, expression_attribute_values


def clusterer_main(run_specifier, batch_job_array_index):
    print('Run Specifier: %s, Batch Job Index: %s' % (
        run_specifier, batch_job_array_index))
    run_id = int(batch_job_array_index)

    config = configparser.RawConfigParser()
    config.read('./template/config_template.conf')
    common_dict = config._sections['common']
    data_dict = config._sections['data']
    # robustness_dict = config._sections['robustness']
    ga_dict = config._sections['GA']

    loc_wlc = mnist_clusterer(**common_dict)
    print('Loading Data')
    train_array_2d, test_array_2d = loc_wlc._load_data(**data_dict)
    print(train_array_2d.shape)
    print(test_array_2d.shape)

    # Extract from Dynamo DB
    cur_task_json_record = extract_dynamodb_record(name=ga_dict['table_name'],
                                                   run_specifier=run_specifier,
                                                   run_id=run_id,
                                                   dynamodb=None,
                                                   region_name=common_dict['region_name'])
    config = json_util.loads(cur_task_json_record['info'])
    print(config)

    print('Calculating Cluster Switch Metrics')

    update_expression, expression_attribute_values = loc_wlc.calculate_cluster_switch_metrics(
        train_array_2d=train_array_2d,
        test_array_2d=test_array_2d,
        embedding_params = config['embedding_params'],
        cluster_params = config['cluster_params'],
        robustness_params = config['robustness_params']
    )
    print(update_expression)
    print(expression_attribute_values)
    # Add this output back to the workload database
    update_dynamodb_info(name=ga_dict['table_name'],
                         hash_str=run_specifier,
                         id=run_id,
                         update_expression=update_expression,
                         expression_attribute_values=expression_attribute_values,
                         dynamodb=None,
                         region_name=common_dict['region_name'])
    # Add this output back to the workload ga database
    update_dynamodb_info(name=ga_dict['ga_detail_table_name'],
                         hash_str=run_specifier,
                         id=run_id,
                         update_expression=update_expression,
                         expression_attribute_values=expression_attribute_values,
                         dynamodb=None,
                         region_name=common_dict['region_name'])


if __name__ == "__main__":
    run_specifier = os.getenv('RUN_SPECIFIER')
    batch_job_array_index = os.getenv('AWS_BATCH_JOB_ARRAY_INDEX')
    # run_specifier = 'NA'
    # batch_job_array_index = 0

    clusterer_main(run_specifier=run_specifier,
                   batch_job_array_index=batch_job_array_index)
