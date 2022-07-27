docker run --runtime nvidia -it -v ${HOME}/.aws/credentials:/root/.aws/credentials:ro -e AWS_BATCH_JOB_ARRAY_INDEX=$AWS_BATCH_JOB_ARRAY_INDEX fmnist_clusterer:latest /bin/bash
