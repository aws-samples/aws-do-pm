## Conda Environment Setup (Local Debugging)

```
conda create -n py37_mnist python=3.7
conda activate py37_mnist
conda install hdbscan
conda install umap-learn
pip install -r requirements.txt

# conda install -c rapidsai cuml

# pip install gpumap hdbscan
```

## Utilizing RAPIDS
```
docker pull rapidsai/rapidsai:21.06-cuda11.0-runtime-ubuntu18.04-py3.7
docker run --runtime=nvidia -it rapidsai/rapidsai:21.06-cuda11.0-runtime-ubuntu18.04-py3.7 /bin/bash

```