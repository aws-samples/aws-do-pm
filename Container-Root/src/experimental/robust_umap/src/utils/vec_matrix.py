import numpy as np
# import umap
# import hdbscan
import itertools
from utils.timeit import timeit
from scipy.sparse import coo_matrix

@timeit
def increment_im_count_v2(cluster_1d):
    # https://cmdlinetips.com/2019/01/3-ways-to-create-sparse-matrix-in-coo-format-with-scipy/
    n_cluster_1d = len(cluster_1d)
    cluster_list = list(np.unique(cluster_1d))

    ret_coo_matrix = coo_matrix((n_cluster_1d, n_cluster_1d))
    for cur_cluster in cluster_list:
        idx_cluster_list = list(np.where(cluster_1d == cur_cluster))[0]
        # Form all iterables
        all_idx_iterables = list(itertools.combinations(idx_cluster_list, 2))
        row_idx = np.array(all_idx_iterables)[:, 0]
        col_idx = np.array(all_idx_iterables)[:, 0]
        data = np.ones(len(row_idx))
        loc_coo_matrix = coo_matrix((data, (row_idx, col_idx)), shape=(n_cluster_1d, n_cluster_1d))
        ret_coo_matrix = ret_coo_matrix + loc_coo_matrix
    return ret_coo_matrix


@timeit
def increment_im_count_v1(cluster_1d, im_count_dict):
    cluster_list = list(np.unique(cluster_1d))
    for cur_cluster in cluster_list:
        idx_cluster_list = list(np.where(cluster_1d == cur_cluster))[0]
        # Form all iterables
        all_idx_iterables = list(itertools.combinations(idx_cluster_list, 2))
        for cur_idx_iterable in all_idx_iterables:
            im_count_dict[cur_idx_iterable] = im_count_dict.get(cur_idx_iterable, 0) + 1

    return im_count_dict

# Convert into deterministic clusters and separate out the Misc
@timeit
def convert_cluster_vec_to_im(cluster_1d, dtype=np.int8):
    n_rows = len(cluster_1d)
    #misc_2d = np.zeros([n_rows, n_rows], dtype=dtype)
    assign_2d = np.zeros([n_rows, n_rows], dtype=dtype)

    cluster_list = list(np.unique(cluster_1d))
    for cur_cluster in cluster_list:
        loc_1d_mask = (cluster_1d == cur_cluster).reshape(-1, 1)
        loc_1d_mask_dtype = loc_1d_mask.astype(dtype)
        loc_2d = (loc_1d_mask_dtype * loc_1d_mask_dtype.transpose()).astype(dtype=dtype)
        assign_2d += loc_2d

    return assign_2d

def _calculate_pdist_from_3d_incidence_matrix(inc_mat_3d):
    (n_runs, n_rows, _) = inc_mat_3d.shape
    # Loop through the axis 0 and assemble the distance matrix
    pdist_list = []
    for i_run in np.arange(n_runs):
        loc_d3d = inc_mat_3d - inc_mat_3d[i_run, :, :]
        loc_d3d_sq = loc_d3d**2
        loc_d3d_sq_dist = np.apply_over_axes(np.sum, loc_d3d_sq, [1, 2])
        pdist_list.append(loc_d3d_sq_dist.squeeze())

    ret_array = np.array(pdist_list)
    # Expect n_rows = n_cols
    ret_array_pct = ret_array/(n_rows**2)
    return ret_array_pct

# def _calculate_run_clusters(pdist_2d, min_dist = 0.01):
#     # Use umap to calculate the clusters based on the precomputed distance matrix
#     U = umap.UMAP(n_neighbors=3, min_dist=min_dist, metric='precomputed')
#     loc_embedding = U.fit_transform(pdist_2d)
#     loc_cluster = hdbscan.HDBSCAN(min_cluster_size=2).fit_predict(loc_embedding)
#     return loc_cluster, loc_embedding

def _calculate_error_given_run_clusters(pdist_2d, run_cluster):
    # Group by clusters and calculate the error per group
    ret_dict = {}
    unique_groups = np.unique(run_cluster)
    for i_cluster in unique_groups:
        loc_idx = (run_cluster == i_cluster)
        avg_error = np.average(pdist_2d[loc_idx, :])
        ret_dict[i_cluster] = avg_error
    return ret_dict

def _calculate_median_given_run_clusters(vec_1d, run_cluster):
    # Group by clusters and calculate the error per group
    ret_dict = {}
    unique_groups = np.unique(run_cluster)
    for i_cluster in unique_groups:
        loc_idx = (run_cluster == i_cluster)
        avg_value = np.median(vec_1d[loc_idx])
        ret_dict[i_cluster] = avg_value
    return ret_dict

def _calculate_sub_run_id_grouping(vec_1d, run_cluster):
    # Group by clusters and calculate the sub runs that are in that cluster
    ret_dict = {}
    unique_groups = np.unique(run_cluster)
    for i_cluster in unique_groups:
        loc_idx = list(np.argwhere(run_cluster==i_cluster).T[0])
        ret_dict[i_cluster] = loc_idx
    return ret_dict


def _calculate_entropy_loss(inc_mat_3d, run_cluster=None):
    (n_runs, n_rows, _) = inc_mat_3d.shape
    eps = np.finfo(float).eps
    ret_dict = {}
    if (run_cluster is None):
        # Do it across all the elements
        # Probability of 1's
        avg_inc_mat_2d = np.average(inc_mat_3d, axis=0)
        # A perfect 0 or 1 state is desirable, any other contributes to entropy
        entropy_avg_inc_mat_2d = avg_inc_mat_2d * np.log(avg_inc_mat_2d + eps) + (1 - avg_inc_mat_2d) * np.log(
            1 - avg_inc_mat_2d + eps)
        ret_dict[0] = -np.average(entropy_avg_inc_mat_2d)
    else:
        # Calculate the entropy of the grouping
        unique_groups = np.unique(run_cluster)
        for i_cluster in unique_groups:
            loc_idx = (run_cluster == i_cluster)
            if(np.sum(loc_idx) > 1):
                # Probability of 1's
                avg_inc_mat_2d = np.average(inc_mat_3d[loc_idx, :, :], axis=0)
                # A perfect 0 or 1 state is desirable, any other contributes to entropy
                entropy_avg_inc_mat_2d = avg_inc_mat_2d * np.log(avg_inc_mat_2d + eps) + (1 - avg_inc_mat_2d) * np.log(1 - avg_inc_mat_2d + eps)
                ret_dict[i_cluster] = -np.average(entropy_avg_inc_mat_2d)
    return ret_dict
