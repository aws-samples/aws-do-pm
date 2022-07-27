import configparser
import json
import pandas as pd
from mnist_clusterer import cluster_data, mnist_clusterer


if __name__ == "__main__":
    config = configparser.RawConfigParser()
    config.read('./template/config_template.conf')
    common_dict = config._sections['common']
    data_dict = config._sections['data']

    loc_mnc = mnist_clusterer(**common_dict)
    train_data, test_data = loc_mnc._load_data(**data_dict)

    with open('./template/workload_config_template.json', 'r') as fp:
        workload_config = json.load(fp)

    # Set the config parameters
    workload_config['embedding_params']['n_neighbors'] = 17
    workload_config['embedding_params']['n_components'] = 6
    workload_config['embedding_params']['min_dist'] = 0.069

    workload_config['cluster_params']['min_samples'] = 6
    workload_config['cluster_params']['eps'] = 0.6502

    results = cluster_data(config = workload_config, train_data=train_data, test_data=test_data, job_num=0)

    train_pd = pd.DataFrame(data=results['embedding_train'])
    train_pd['cluster'] = results['cluster_train']
    train_pd['type'] = 0

    test_pd = pd.DataFrame(data=results['embedding_test'])
    test_pd['cluster'] = results['cluster_test']
    test_pd['type'] = 1
    export_pd = pd.concat([train_pd, test_pd])
    export_pd.to_csv('./export_run.csv', index=False)
