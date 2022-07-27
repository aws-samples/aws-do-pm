DeDuplicate the vectors using FAISS based similarity

Copy the data files into the wd
cd wd
aws s3 sync s3://mldatastore/faiss/quora_question_pairs ./quora_question_pairs/raw

Convert to parquet files
```
python script_preprocess.py --in_csv_file /app/wd/quora_question_pairs/raw/train.csv --out_pq_file /app/wd/quora_question_pairs/raw/train.pq
python script_preprocess.py --in_csv_file /app/wd/quora_question_pairs/raw/test.csv --out_pq_file /app/wd/quora_question_pairs/raw/test.pq
```

Convert it into sentence embedding and save it to ./quora_question_pairs/embedding

```
python script_embedding.py --in_pq_file /app/wd/quora_question_pairs/raw/train.pq --out_npy_file /app/wd/quora_question_pairs/embedding/train.npy
python script_embedding.py --in_pq_file /app/wd/quora_question_pairs/raw/test.pq --out_npy_file /app/wd/quora_question_pairs/embedding/test.npy
```

Train the FAISS model

```
python script_faiss_train.py --in_npy_file /app/wd/quora_question_pairs/embedding/train.npy --out_model_file /app/wd/quora_question_pairs/model/faiss_model_1.obj --num_partitions 128
```

Query the Model

```
python script_faiss_nn.py --in_npy_file /app/wd/quora_question_pairs/embedding/test.npy --in_model_file /app/wd/quora_question_pairs/model/faiss_model_1.obj --num_neighbors 2 --out_nn_file /app/wd/quora_question_pairs/results/test_nn.obj
```
