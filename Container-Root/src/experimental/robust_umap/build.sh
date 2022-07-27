#!/bin/bash

if [[ "$#" -eq 0 ]]; then
  echo "Image Name set to fmnist_clusterer:latest"
  export IMG_NAME=fmnist_clusterer
  export IMG_TAG=latest
  export IMG_NAME_TAG=$IMG_NAME:$IMG_TAG
else
  echo "Image named: $1"
  export IMG_NAME_TAG=$1
fi

echo "Building..."
docker build -t $IMG_NAME_TAG .

echo "Done"
