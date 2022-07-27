from tqdm import tqdm
import argparse
import pathlib
import pyarrow as pa
import pyarrow.parquet as pq
import numpy as np
import pandas as pd
from itertools import islice
from sentence_transformers import SentenceTransformer

def group_elements(lst, chunk_size):
    lst = iter(lst)
    return iter(lambda: tuple(islice(lst, chunk_size)), ())


def process_file(in_pq, chunk_size = 500):
    model = SentenceTransformer('all-MiniLM-L6-v2').cuda()
    df = pd.read_parquet(in_pq)
    # Extract the text column
    sentence_list = list(df['text'])
    overall_embedding_list = []
    num_chunks = int(len(sentence_list)/chunk_size)+1
    print('Sentence Size: %d, Num Chunks: %d'%(len(sentence_list), num_chunks))
    for cur_list in tqdm(group_elements(sentence_list, chunk_size), total=num_chunks):
        loc_list = model.encode(cur_list)
        overall_embedding_list.extend(loc_list)
    ret_embedding = np.vstack(overall_embedding_list)
    return ret_embedding

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--in_pq_file', help='In Parquet Filename')
    parser.add_argument('--out_npy_file', help='Out Numpy Filename')
    args = parser.parse_args()

    ret_embedding = process_file(in_pq=args.in_pq_file, chunk_size=500)

    # Create the parent directory structure
    p = pathlib.Path(args.out_npy_file)
    p.parent.mkdir(parents=True, exist_ok=True)
    np.save(args.out_npy_file, ret_embedding, allow_pickle=True, fix_imports=True)
