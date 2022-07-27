#!/bin/bash

# Login to container registry

if [ -f ./config.properties ]; then
    source ./config.properties
elif [ -f ../config.properties ]; then
    source ../config.properties
else
    echo "config.properties not found!"
fi

case "$registry_type" in
    "ecr")
        echo "Logging in to $registry_type $registry ..."
        aws ecr get-login-password --region $region | docker login --username AWS --password-stdin $registry
        ;;
    *)
        echo "Login for registry_type=$registry_type is not implemented"
        ;;
esac