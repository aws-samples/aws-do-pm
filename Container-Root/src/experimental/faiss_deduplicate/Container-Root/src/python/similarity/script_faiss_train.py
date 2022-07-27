import os
import argparse
import pathlib
import faiss
import numpy as np
import matplotlib.pyplot as plt

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--in_npy_file', help='In Numpy Filename')
    parser.add_argument('--num_partitions', type=int, help='Number of Partitions (128)')
    parser.add_argument('--out_model_file', help='Out Model Filename')
    args = parser.parse_args()

    # https://www.programcreek.com/python/example/112286/faiss.IndexIVFFlat
    d_array = np.load(args.in_npy_file)
    embedding_dim = d_array.shape[1]
    num_partitions = args.num_partitions
    quantizer = faiss.IndexFlatL2(embedding_dim)
    index = faiss.IndexIVFFlat(quantizer, embedding_dim, num_partitions)
    index.train(d_array)
    index.add(d_array)
    print('FAISS Training Status: %x'%(index.is_trained))

    # Create the parent directory structure
    p = pathlib.Path(args.out_model_file)
    p.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, args.out_model_file)


    # https://searchcode.com/file/309450552/benchs/distributed_ondisk/make_index_vslice.py/
    index_ivf = faiss.extract_index_ivf(index)
    print('invlists stats: imbalance %.3f' % index_ivf.invlists.imbalance_factor())
    index_ivf.invlists.print_stats()

    il = faiss.extract_index_ivf(index).invlists
    list_sizes = [il.list_size(i) for i in range(il.nlist)]
    # print(list_sizes)
    fig, ax = plt.subplots(1, 2, figsize=(12, 8))
    ax[0].hist(list_sizes, bins=40)
    ax[0].grid()
    ax[0].set_title('Histogram (#Cluster = %d)'%(num_partitions))
    ax[0].set_xlabel('# Elements in Cluster')
    ax[1].boxplot(list_sizes)
    ax[1].grid()
    ax[1].set_ylabel('# Elements in Cluster')
    file_prefix, file_suffix = os.path.splitext(args.out_model_file)
    png_filename = '%s_%d.png'%(file_prefix, num_partitions)
    plt.savefig(png_filename)

