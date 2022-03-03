#!/bin/bash

######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

# Function to check if container is running in privileged mode
function isPrivileged ()
{
    if [ $(ip link ls | grep dummy0 | wc -l) -eq 1 ]; then
	ip link delete dummy0 >/dev/null
    fi
    ip link add dummy0 type dummy >/dev/null
    if [ $? -eq 0 ]; then
	export PRIVILEGED=true
        # clean the dummy0 link
        ip link delete dummy0 >/dev/null
        echo "Container is running in privileged mode."
    else
        export PRIVILEGED=false
        echo "Container is running in non-privileged mode."
    fi
}

# Start docker-in-docker if container is privileged
isPrivileged
if [ "${PRIVILEGED}" == "true" ]; then
    service docker start
fi

# Initialize container
/init.sh

# Start UI
#streamlit run /src/python/ui/main_app.py --server.port ${PM_UI_PORT_INT} &

# Infinite loop to help the container stay up even if UI is not up
while true; do 
	echo "$(date): Container is up"
	sleep 3600
done
