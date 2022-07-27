#!/bin/bash

source ./config.properties

action=$1
if [ "$action" == "" ]; then

	echo ""
	echo "Building base container ..."
	
  docker build -t ${registry}${image_name}${image_tag} -f ./Dockerfile .

elif [ "$action" == "push" ]; then
	./1-build/push.sh
elif [ "$action" == "pull" ]; then
	./-build/pull.sh
fi
