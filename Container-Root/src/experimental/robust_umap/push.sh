echo "Logging into ECR"
aws ecr get-login-password --region us-east-1 | docker login --username AWS \
    --password-stdin 561120826261.dkr.ecr.us-east-1.amazonaws.com

echo "Tagging fmnist_clusterer for Registry Push"
docker tag fmnist_clusterer 561120826261.dkr.ecr.us-east-1.amazonaws.com/fmnist_clusterer

echo "Pushing to ECR"
docker push 561120826261.dkr.ecr.us-east-1.amazonaws.com/fmnist_clusterer

echo "Done"
