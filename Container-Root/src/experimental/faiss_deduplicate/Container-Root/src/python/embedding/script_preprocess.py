import argparse
import pathlib
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd

def process_csv(in_csv):
    df = pd.read_csv(in_csv)
    # Extract the 2 columns and make it into one long dataset
    df_1 = pd.DataFrame()
    df_1['text'] = df['question1']
    df_2 = pd.DataFrame()
    df_2['text'] = df['question2']
    df_concat = pd.concat([df_1, df_2])
    df_table = pa.Table.from_pandas(df_concat)
    return df_table

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--in_csv_file', help='In CSV Filename')
    parser.add_argument('--out_pq_file', help='Out Parquet Filename')
    args = parser.parse_args()

    ret_table = process_csv(in_csv=args.in_csv_file)

    # Create the parent directory structure
    p = pathlib.Path(args.out_pq_file)
    p.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(ret_table, args.out_pq_file, compression=None)
