#!/bin/bash

######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

# Generate sample EV dataset

if [ "${NUM_VEHICLES}" == "" ]; then
    NUM_VEHICLES=10
fi

if [ "${NUM_ROUTES}" == "" ]; then
    NUM_ROUTES=10
fi

if [ "${DEST_PATH}" == "" ]; then
    DEST_PATH=/wd
fi

mkdir -p ${DEST_PATH}

envsubst < /src/python/example/ev/task/task_ev_data_generate_template.json > ${DEST_PATH}/task_ev_data_generate.json

python /src/python/example/ev/technique/ev_datagen_em/norm_route_generator.py --config ${DEST_PATH}/task_ev_data_generate.json
