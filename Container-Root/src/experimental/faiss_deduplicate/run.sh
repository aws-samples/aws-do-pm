#!/bin/bash

source ./config.properties

echo ""
echo "Opening bash shell in container"
docker run --gpus 0 -it --rm -v $(pwd)/wd:/app/wd -v $(pwd)/Container-Root/src:/src ${registry}${image_name}${image_tag} /bin/bash
