import argparse
import pathlib
from tqdm import tqdm
import joblib
import faiss
import numpy as np

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--in_npy_file', help='In Numpy Filename')
    parser.add_argument('--in_model_file', help='In Model Filename')
    parser.add_argument('--num_neighbors', type=int, help='In Model Filename (1)')
    parser.add_argument('--out_nn_file', help='Out Nearest Neighbors Filename')

    args = parser.parse_args()

    d_array = np.load(args.in_npy_file)[0:100000, :]
    # index = joblib.load(args.in_model_file)
    index = faiss.read_index(args.in_model_file)

    res = faiss.StandardGpuResources()
    index_gpu = faiss.index_cpu_to_gpu(res, 0, index)

    chunk_size = 1000
    num_chunks = int(d_array.shape[0]/chunk_size)
    split_d_array = np.array_split(d_array, num_chunks)
    ret_list = []
    for cur_np_array in tqdm(split_d_array):
        D, I = index_gpu.search(cur_np_array, args.num_neighbors)
        ret_list.append([D, I])

    # Create the parent directory structure
    p = pathlib.Path(args.out_nn_file)
    p.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(ret_list, args.out_nn_file)

