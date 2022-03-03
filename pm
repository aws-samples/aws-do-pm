#!/bin/bash

# Predictive Modeling Command Line Interface

source .env

if [ ! -d wd ]; then
	mkdir wd
fi 

if [ "$TO" == docker ]; then
	echo $PM_TO > wd/.to
	source .env
fi

if [[ "$1" == "" || "$1" == "--help" ]]; then
	help
	exit 0
fi

stty sane

if [ "$1" == "config" ]; then
	case "$2" in
		"ls")
			echo ""
			echo "${PM_CONFIG_ITEMS[*]}"
			echo ""
			;;
		"show")
			if [ "$3" == "" ]; then
				config_show
			else
				if [[ " ${PM_CONFIG_ITEMS[*]} " =~ " $3 " ]]; then
					echo "${3}: ${!3}"
				else
					echo "Item $3 is not part of the standard configuration"
				fi
			fi
			;;
		"set")
			if [ ! "$4" == "" ]; then
				./config.sh "$3" "$4"
			elif [ ! "$3" == "" ]; then
				if [[ " ${PM_CONFIG_ITEMS[*]} " =~ " $3 " ]]; then
					read -r -p "Enter value for $3 [Enter=${!3}]: " newval
					if [ ! "$newval" == "" ]; then
						./config.sh $3 "$newval"
					fi
				else
					echo "Item $3 is not recognized as part of the standard configuration"
				fi
			else
				for index in ${!PM_CONFIG_ITEMS[@]}; do
                			CONFIG_ITEM_NAME=${PM_CONFIG_ITEMS[$index]}
                			CONFIG_ITEM_VALUE=${!CONFIG_ITEM_NAME}
					read -r -p "Enter value for ${CONFIG_ITEM_NAME} [Enter=${CONFIG_ITEM_VALUE}]: " newval
				        if [ ! "$newval" == "" ]; then
                                                ./config.sh ${CONFIG_ITEM_NAME} "$newval"
                                        fi
				done
			fi
			;;
		"--help")
			help_config
			;;
		*)
			echo "ERROR: Unrecognized config command $2"
			help_config
			;;
	esac
elif [ "$1" == "system" ]; then
	case "$2" in
		"init")
			NUM_PLATFORM_CONTAINERS=$(./status.sh | grep platform | grep -v ui | wc -l)
			i=1
			while [ $i -le $NUM_PLATFORM_CONTAINERS ]; do
			    ./exec.sh platform $i bash -c \"mkdir -p ${PM_ROOT_PATH}/tmp/$i \; echo $i \> .idx\"
			    i=$((i+1))
			done		
			if [ "$AWS_DEFAULT_REGION" == "us-east-1" ]; then
				./exec.sh platform $IDX aws "$AWS_OPTS" s3api create-bucket --bucket ${PM_S3_BUCKET} #--create-bucket-configuration LocationConstraint=${AWS_DEFAULT_REGION}
			else
				./exec.sh platform $IDX aws "$AWS_OPTS" s3api create-bucket --bucket ${PM_S3_BUCKET} --create-bucket-configuration LocationConstraint=${AWS_DEFAULT_REGION}
			fi
			./exec.sh platform $IDX mkdir -p ${PM_ROOT_PATH}/data ${PM_ROOT_PATH}/model ${PM_ROOT_PATH}/asset ${PM_ROOT_PATH}/technique ${PM_ROOT_PATH}/task ${PM_ROOT_PATH}/service ${PM_ROOT_PATH}/error ${PM_ROOT_PATH}/trash 
            		./exec.sh platform $IDX python /src/python/lib/db/graph/graph_init.py
			./exec.sh platform $IDX python /src/python/pm/task/task_register_system_techniques.py
			if [ "$OPERATING_SYSTEM" == "Linux" ]; then
				USR=$(whoami)
				if [ ! "$USR" == "root" ]; then
					echo "Setting owner of wd/tmp to $USER ..."
					sudo chown -R $USER:$USER wd/tmp
				fi
			fi
			;;
		"clear")
			echo "Removing services ..."
			./exec.sh platform $IDX python /src/python/pm/service/services_destroy.py
			if [ "$TO" == "kubernetes" ]; then
				kubectl delete service $(kubectl get service | grep service | cut -d ' ' -f 1)
				kubectl delete pod $(kubectl get pod | grep task | cut -d ' ' -f 1)
			fi
			echo "Clearing graph database ..."
			./exec.sh platform $IDX python /src/python/lib/db/graph/graph_clear.py
			echo "Clearing local storage ..."
			./exec.sh platform $IDX rm -rf ${PM_ROOT_PATH}/data ${PM_ROOT_PATH}/model ${PM_ROOT_PATH}/asset ${PM_ROOT_PATH}/technique ${PM_ROOT_PATH}/task ${PM_ROOT_PATH}/service ${PM_ROOT_PATH}/error ${PM_ROOT_PATH}/trash ${PM_ROOT_PATH}/tmp
			echo "Clearing cloud storage ..."
			./exec.sh platform $IDX aws "$AWS_OPTS" s3 rb s3://${PM_S3_BUCKET} --force
			;;
		"--help")
			help_system
			;;
		*)
			echo "ERROR: Unrecognized system command $2"
			help_system
			;;
	esac
elif [ "$1" == "technique" ]; then
	case "$2" in
		"ls")
			if [ "$3" == "" ]; then
				./exec.sh platform $IDX python /src/python/pm/technique/technique.py --action ls 
			else
				./exec.sh platform $IDX python /src/python/pm/technique/technique.py --action ls --tags $3 $4 $5 $6 $7 $8 $9
			fi
			;;
		"describe")
			if [ "$3" == "" ]; then
					echo "Please specify technique_id as argument"
					help_technique
			else
				./exec.sh platform $IDX bash -c \"python /src/python/pm/technique/technique.py --action describe --technique_id $3 \"
			fi
			;;
		"template")
			if [ "$3" == "" ]; then
				echo "Please specify technique_id as argument"
				help_technique
			else
				./exec.sh platform $IDX bash -c \"python /src/python/pm/technique/technique.py --action template --technique_id $3 \"
			fi
			;;
		"register")
			if [ "$3" == "" ]; then
				echo "Please specify path to the technique registration json"
				help_technique
			else
				./exec.sh platform $IDX python /src/python/pm/task/task_technique_register.py --config $3
			fi
			;;
		"remove")
			if [ "$3" == "" ]; then
				echo "Please specify technique_id as argument"
				help_technique
			else
				./exec.sh platform $IDX bash -c \"python /src/python/pm/technique/technique.py --action delete --technique_id $3 \"
			fi
			;;
		"--help")
			help_technique
			;;
		*)
			echo "ERROR: Unrecognized technique command $2"
			help_technique
			;;
	esac
elif [ "$1" == "go" ]; then
	if [ "$2" == "--help" ]; then
		echo ""
		echo "$0 go [tags] - generates a template from the technique, matching the specified tags"
		echo ""
		echo "   Available techniques and tags:"
		./exec.sh platform $IDX python /src/python/pm/technique/technique.py --action ls
		echo ""
	elif [ "$2" == "" ]; then
		./exec.sh platform $IDX python /src/python/pm/technique/technique.py --action search
	else
		OUTPUT=$(QUIET=true ./exec.sh platform $IDX python /src/python/pm/technique/technique.py --action search --tags ${@:2})
		FIRST_CHAR=${OUTPUT:0:1}
		if [ "${FIRST_CHAR}" == "{" ]; then
			echo "${OUTPUT}" > ${PM_ROOT_PATH}/tmp/${IDX}/input.json
			if [ "$QUIET" == "false" ]; then
				echo "" 1>&2
				echo "Content was saved to file ${PM_ROOT_PATH}/tmp/input.json" 1>&2
				echo "After editing the file, it can be executed using the following command:" 1>&2
				echo "$0 do ${PM_ROOT_PATH}/tmp/${IDX}/input.json" 1>&2
				echo "" 1>&2
			fi
		fi
		echo "${OUTPUT}"
	fi
elif [ "$1" == "do" ]; then
	if [ "$2" == "--help" ]; then
		help_do
	else
		if [ "$2" == "" ]; then
			INPUT_JSON_PATH=${PM_ROOT_PATH}/tmp/${IDX}/input.json
		else
			INPUT_JSON_PATH=$2
		fi
		./exec.sh platform $IDX python /src/python/pm/task/task.py --action run --config ${INPUT_JSON_PATH}
	fi
elif [ "$1" == "data" ]; then
	case "$2" in
		"ls")
			./exec.sh platform $IDX python /src/python/pm/data/data.py --action ls
			;;
		"describe")
			if [ "$3" == "" ]; then
				echo ""
				echo "ERROR: Please specify a dataset id"
				help_data
			else
				./exec.sh platform $IDX bash -c \"python /src/python/pm/data/data.py --action describe --id $3 \"
			fi
			;;
		"register")
			if [ "$3" == "" ]; then
				echo "Please specify data folder path"
				help_data
			elif [ "$4" == "" ]; then
				echo "Please specify main filename after the data folder path"
				help_data
			else
				FILENAME=$4
				DESCRIPTION="Registered dataset"
				if [ ! "$5" == "" ]; then
					DESCRIPTION="$5"
				fi
				LOCAL_PATH=$3
#				if [ ! "${LOCAL_PATH:0:1}" == "/" ]; then
#					LOCAL_PATH=$(pwd)/$3
#				fi
				echo ""
				echo "Registering data from local path: $LOCAL_PATH"
				TIMESTAMP=$(date +%Y%m%d%H%M%S%3N)
				FOLDER_NAME=$(basename ${LOCAL_PATH})
				TMP_DEST_PATH=${PM_ROOT_PATH}/tmp/${IDX}/${FOLDER_NAME}-${TIMESTAMP}
				echo "Temporary destination path: $TMP_DEST_PATH"
				mkdir -p ${TMP_DEST_PATH}
				./cp-to.sh platform $IDX ${LOCAL_PATH} ${TMP_DEST_PATH}
				echo "{\"technique_name\": \"data_registration\",\"task_options\": [\"-it\",\"--rm\",\"-e\", \"AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION\", \"-e\", \"AWS_OPTS=$AWS_OPTS\"],\"analyticSettings\": { \"pm_s3_bucket\": \"${PM_S3_BUCKET}\", \"pm_root_path\": \"${PM_ROOT_PATH}\",\"local_path\": \"${TMP_DEST_PATH}/${FOLDER_NAME}\",\"filename\":\"${FILENAME}\",\"description\": \"${DESCRIPTION}\"}}" > ${PM_ROOT_PATH}/tmp/${IDX}/task_data_register_${TIMESTAMP}.json
				./cp-to.sh platform $IDX ${PM_ROOT_PATH}/tmp/${IDX}/task_data_register_${TIMESTAMP}.json ${PM_ROOT_PATH}/tmp/${IDX}/task_data_register_${TIMESTAMP}.json
				./exec.sh platform $IDX bash -c \"python3 /src/python/pm/task/task.py --action run --config ${PM_ROOT_PATH}/tmp/${IDX}/task_data_register_${TIMESTAMP}.json\"
			fi
			;;
		"delete")
			if [ "$3" = "" ]; then
				echo ""
				echo "ERROR: Please specify data id"
				help_data
			else
				./exec.sh platform $IDX bash -c \"python /src/python/pm/data/data.py --action delete --id $3\"
			fi
			;;
		"--help")
			help_data
			;;
		*)
			echo "ERROR: Unrecognized data command $2"
			help_data
			;;
	esac
elif [ "$1" == "model" ]; then
	case $2 in
		"--help")
			help_model
			;;
		"ls")
			./exec.sh platform $IDX python /src/python/pm/model/model.py --action ls
			;;
		"describe")
                        if [ "$3" == "" ]; then
                                echo ""
                                echo "ERROR: Please specify a model id"
                                help_model
                        else
                                ./exec.sh platform $IDX bash -c \"python /src/python/pm/model/model.py --action describe --id $3 \"
                        fi
			;;
		"register")
			if [ "$4" == "" ]; then
				echo "Please specify model file path relative to the model directory"
				help_model
			else
				LOCAL_PATH=$3
    			if [ ! "${LOCAL_PATH:0:1}" == "/" ]; then
    				LOCAL_PATH=${PROJECT_HOME}/$3
                fi
				REL_MODEL_FILEPATH=$4
    			DESCRIPTION="Registered model"
			    if [ ! "$5" == "" ]; then
					DESCRIPTION="$5"
			    fi
			    echo ""
			    echo "Registering model from local path: $LOCAL_PATH"
			    TIMESTAMP=$(date +%Y%m%d%H%M%S%3N)
			    FOLDER_NAME=$(basename ${LOCAL_PATH})
				TMP_DEST_PATH=${PM_ROOT_PATH}/tmp/${IDX}/${FOLDER_NAME}-${TIMESTAMP}
				mkdir -p ${TMP_DEST_PATH}
			    echo "{\"technique_name\": \"model_registration\",\"task_options\": [\"-it\",\"--rm\",\"-v\",\"${LOCAL_PATH}:/register\", \"-e\", \"AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION\", \"-e\", \"AWS_OPTS=$AWS_OPTS\"],\"analyticSettings\": { \"pm_s3_bucket\": \"${PM_S3_BUCKET}\", \"pm_root_path\": \"${PM_ROOT_PATH}\",\"local_path\": \"${TMP_DEST_PATH}/${FOLDER_NAME}\",\"rel_model_filepath\":\"${REL_MODEL_FILEPATH}\", \"description\": \"${DESCRIPTION}\"}}" > ${PM_ROOT_PATH}/tmp/${IDX}/task_model_register_${TIMESTAMP}.json
			    ./cp-to.sh platform $IDX ${PM_ROOT_PATH}/tmp/${IDX}/task_model_register_${TIMESTAMP}.json ${PM_ROOT_PATH}/tmp/${IDX}/task_model_register_${TIMESTAMP}.json
			    ./exec.sh platform $IDX bash -c \"python3 /src/python/pm/task/task.py --action run --config ${PM_ROOT_PATH}/tmp/${IDX}/task_model_register_${TIMESTAMP}.json\"
			fi
			;;
		"build")
			if [ ! "$3" == "" ]; then
				DATA_ID=$3
				TASK_JSON=$(./pm go build ann model)
				TASK_ID=$(echo "${TASK_JSON}" | jq -r .task_id)
				MODEL_ID=$(echo "${TASK_JSON}" | jq -r '.output_artifacts.model|.[0]')
				echo "${TASK_JSON}" | sed -e "s/<data_id>/${DATA_ID}/g" > ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_model_build_ann.json
				./cp-to.sh platform $IDX ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_model_build_ann.json ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_model_build_ann.json
				./pm do ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_model_build_ann.json
				./exec.sh platform $IDX aws "$AWS_OPTS" s3 sync ${PM_ROOT_PATH}/model/${MODEL_ID} s3://${PM_S3_BUCKET}/model/${MODEL_ID}
			else
				echo "Please specify DATA_ID as argument"
			fi
			;;
		"predict")
			if [ "$4" == "" ]; then
				echo "Please specify  (model_id or service_id) and data_id as arguments"
				help_model
				exit 1
			fi
			MODEL_OR_SERVICE_ID=$3
			DATA_ID=$4
			
			IS_MODEL=$(./pm model ls | grep $MODEL_OR_SERVICE_ID > /dev/null; echo $?)
			IS_SERVICE=$(./pm service ls | grep $MODEL_OR_SERVICE_ID > /dev/null; echo $?)

			DESTROY_SERVICE=No
			if [ "$IS_SERVICE" == "0" ]; then
				SERVICE_ID=$MODEL_OR_SERVICE_ID
				MODEL_ID_RAW=$(./pm service describe ${MODEL_OR_SERVICE_ID} | grep model_id | cut -d '"' -f 4)
				MODEL_ID=${MODEL_ID_RAW:0:${PM_ID_LENGTH}}
			elif [ "$IS_MODEL" == "0" ]; then
				DESTROY_SERVICE=Yes
				MODEL_ID=$MODEL_OR_SERVICE_ID
				SERVICE_ID_RAW=$(./pm service deploy ${MODEL_ID} | grep service/ | cut -d '/' -f 2)
				SERVICE_ID=${SERVICE_ID_RAW:0:$PM_ID_LENGTH}
			else
				echo "Could not identify ID $MODEL_OR_SERVICE_ID as a model or a service."
				echo "Please specify model or service id, and data id"
				help_model
				exit 1
			fi
			
			TASK_JSON=$(./pm go model predict grpc)
			TASK_ID=$(echo "${TASK_JSON}" | jq -r .task_id)
			PREDICTED_DATA_ID=$(echo "${TASK_JSON}" | jq -r '.output_artifacts.data|.[0]')
			echo "${TASK_JSON}" | sed -e "s/<data_id>/${DATA_ID}/g" -e "s/<model_id>/${MODEL_ID}/g" -e "s/<service_id>/${SERVICE_ID}/g"  > ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_model_predict_grpc.json
			./cp-to.sh platform $IDX ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_model_predict_grpc.json ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_model_predict_grpc.json
			./pm do ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_model_predict_grpc.json
			./exec.sh platform $IDX aws "$AWS_OPTS" s3 sync ${PM_ROOT_PATH}/data/${PREDICTED_DATA_ID} s3://${PM_S3_BUCKET}/data/${PREDICTED_DATA_ID}

			if [ "${DESTROY_SERVICE}" == "Yes" ]; then
				RESULT=$(./pm service destroy ${SERVICE_ID})
			fi
			;;
		"update")
			if [ "$4" == "" ]; then
				echo "Please specify  (model_id or service_id) and data_id as arguments"
				help_model
				exit 1
			fi
			MODEL_OR_SERVICE_ID=$3
			DATA_ID=$4
			
			IS_MODEL=$(./pm model ls | grep $MODEL_OR_SERVICE_ID > /dev/null; echo $?)
			IS_SERVICE=$(./pm service ls | grep $MODEL_OR_SERVICE_ID > /dev/null; echo $?)

			DESTROY_SERVICE=No
			if [ "$IS_SERVICE" == "0" ]; then
				SERVICE_ID=$MODEL_OR_SERVICE_ID
				MODEL_ID_RAW=$(./pm service describe ${MODEL_OR_SERVICE_ID} | grep model_id | cut -d '"' -f 4)
				MODEL_ID=${MODEL_ID_RAW:0:${PM_ID_LENGTH}}
			elif [ "$IS_MODEL" == "0" ]; then
				DESTROY_SERVICE=Yes
				MODEL_ID=$MODEL_OR_SERVICE_ID
				SERVICE_ID_RAW=$(./pm service deploy ${MODEL_ID} | grep service/ | cut -d '/' -f 2)
				SERVICE_ID=${SERVICE_ID_RAW:0:$PM_ID_LENGTH}
			else
				echo "Could not identify ID $MODEL_OR_SERVICE_ID as a model or a service."
				echo "Please specify model or service id, and data id"
				help_model
				exit 1
			fi

			TASK_JSON=$(./pm go update model ukf grpc)
			TASK_ID=$(echo "${TASK_JSON}" | jq -r .task_id)
			UPDATED_MODEL_ID=$(echo "${TASK_JSON}" | jq -r '.output_artifacts.model|.[0]')
			echo "${TASK_JSON}" | sed -e "s/<model_id>/${MODEL_ID}/g" -e "s/<service_id>/${SERVICE_ID}/g" -e "s/<data_id>/${DATA_ID}/g" > ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_model_update_ukf_grpc.json
			./cp-to.sh platform 1 ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_model_update_ukf_grpc.json ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_model_update_ukf_grpc.json
			./pm do ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_model_update_ukf_grpc.json
			./exec.sh platform 1 aws "$AWS_OPTS" s3 sync ${PM_ROOT_PATH}/model/${UPDATED_MODEL_ID} s3://${PM_S3_BUCKET}/model/${UPDATED_MODEL_ID}

			if [ "${DESTROY_SERVICE}" == "Yes" ]; then
				RESULT=$(./pm service destroy ${SERVICE_ID})
			fi
			;;
		"sensitivity")
			if [ "$4" == "" ]; then
				echo "Please specify  (model_id or service_id) and data_id as arguments"
				help_model
				exit 1
			fi
			MODEL_OR_SERVICE_ID=$3
			DATA_ID=$4
			
			IS_MODEL=$(./pm model ls | grep $MODEL_OR_SERVICE_ID > /dev/null; echo $?)
			IS_SERVICE=$(./pm service ls | grep $MODEL_OR_SERVICE_ID > /dev/null; echo $?)

			DESTROY_SERVICE=No
			if [ "$IS_SERVICE" == "0" ]; then
				SERVICE_ID=$MODEL_OR_SERVICE_ID
				MODEL_ID_RAW=$(./pm service describe ${MODEL_OR_SERVICE_ID} | grep model_id | cut -d '"' -f 4)
				MODEL_ID=${MODEL_ID_RAW:0:${PM_ID_LENGTH}}
			elif [ "$IS_MODEL" == "0" ]; then
				DESTROY_SERVICE=Yes
				MODEL_ID=$MODEL_OR_SERVICE_ID
				SERVICE_ID_RAW=$(./pm service deploy ${MODEL_ID} | grep service/ | cut -d '/' -f 2)
				SERVICE_ID=${SERVICE_ID_RAW:0:$PM_ID_LENGTH}
			else
				echo "Could not identify ID $MODEL_OR_SERVICE_ID as a model or a service."
				echo "Please specify model or service id, and data id"
				help_model
				exit 1
			fi

			TASK_JSON=$(./pm go analyze model sensitivity sobol grpc)
			TASK_ID=$(echo "${TASK_JSON}" | jq -r .task_id)
			SENSITIVITY_DATA_ID=$(echo "${TASK_JSON}" | jq -r '.output_artifacts.data|.[0]')
			echo "${TASK_JSON}" | sed -e "s/<model_id>/${MODEL_ID}/g" -e "s/<service_id>/${SERVICE_ID}/g" -e "s/<data_id>/${DATA_ID}/g" > ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_model_sensitivity_grpc.json
			./cp-to.sh platform $IDX ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_model_sensitivity_grpc.json ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_model_sensitivity_grpc.json
			./pm do ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_model_sensitivity_grpc.json
			./exec.sh platform $IDX aws "$AWS_OPTS" s3 sync ${PM_ROOT_PATH}/data/${SENSITIVITY_DATA_ID} s3://${PM_S3_BUCKET}/model/${SENSITIVITY_DATA_ID}
			
			if [ "${DESTROY_SERVICE}" == "Yes" ]; then
				RESULT=$(./pm service destroy ${SERVICE_ID})
			fi
			;;
		*)
			echo "ERROR: Unrecognized model command $2"
			help_model
			;;
	esac
elif [ "$1" == "service" ]; then
    case $2 in
        "--help")
        	help_service
        	;;
        "ls")
			./exec.sh platform $IDX python /src/python/pm/service/service.py --action ls
			;;
        "deploy")
			if [ "$3" == "" ]; then
				echo "Please specify model ID as argument"
				help_service
			else
				TASK_JSON=$(./pm go serve model grpc)
				TASK_ID=$(echo "${TASK_JSON}" | jq -r .task_id)
				SERVICE_ID=$(echo "${TASK_JSON}" | jq -r .output_artifacts.service[0])
				PORT_NUM=$(echo "${TASK_JSON}" | jq -r .analyticSettings.internal_port)
				echo "${TASK_JSON}" | sed -e "s/<model_id>/$3/g" | sed -e "s/<group_id>/$IDX/g" > ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_model_serve_grpc.json
				./cp-to.sh platform $IDX ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_model_serve_grpc.json ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_model_serve_grpc.json
				./pm do ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_model_serve_grpc.json
            	if [ "$TO" == "kubernetes" ]; then
            		# Expose service
            		sleep 1
            		echo "Exposing pod task-${TASK_ID} as a service ..."
            		kubectl expose pod task-${TASK_ID} --port=${PORT_NUM} --name service-${SERVICE_ID} 
            	fi
				echo "SERVICE_ID=$SERVICE_ID"                  		
			fi
			;;
		"describe")
			if [ "$3" == "" ]; then
				echo "Please specify service ID as argument"
				help_service
			else
				./exec.sh platform $IDX bash -c \"python /src/python/pm/service/service.py --action describe --id $3 \| jq .  \"
			fi
			;;
		"status")
			if [ "$3" == "" ]; then
				echo "Please specify service ID as argument"
				help_service
			else
				./exec.sh platform $IDX bash -c \"python /src/python/pm/service/service.py --action status --id $3\"
			fi
			;;
		"configure")
			if [ "$4" == "" ]; then
				echo "Please specify service ID and model ID as arguments"
				help_service
			else
				TASK_JSON=$(./pm go configure model service)
				TASK_ID=$(echo "${TASK_JSON}" | jq -r .task_id)
				echo "${TASK_JSON}" | sed -e "s/<service_id>/$3/g" | sed -e "s/<model_id>/$4/g" > ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_service_configure.json
				./cp-to.sh platform $IDX ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_service_configure.json ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_service_configure.json
				./pm do ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_service_configure.json
			fi
			;;
		"destroy")
			if [ "$3" == "" ]; then
				echo "Please specify service ID as argument"
				help_service
			else
				TASK_JSON=$(./pm go destroy service)
				FIRST_CHAR=${TASK_JSON:0:1}
				if [ ! "${TASK_JSON}" == "" ]; then 
					if [ ! "$FIRST_CHAR" == "{" ]; then
						TASK_JSON="{${TASK_JSON}"
					fi
				fi
				TASK_ID=$(echo "${TASK_JSON}" | jq -r .task_id)
				echo "${TASK_JSON}" | sed -e "s/<service_id>/$3/g" > ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_service_destroy.json
				./cp-to.sh platform $IDX ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_service_destroy.json ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_service_destroy.json
				./pm do ${PM_ROOT_PATH}/tmp/${IDX}/task_${TASK_ID}_service_destroy.json
			fi
			;;
		*)
			echo "ERROR: Unrecognized service command $2"
			help_service
			;;
	esac
elif [ "$1" == "task" ]; then
        case $2 in
                "--help")
                        help_task
                        ;;
                "ls")
                        ./exec.sh platform $IDX python /src/python/pm/task/task.py --action ls
                        ;;
                "describe")
			./exec.sh platform $IDX bash -c \"python /src/python/pm/task/task.py --action describe --task $3 \"
			;;
		"template")
			if [ "$4" == "" ]; then
				echo "Please specify technique_id and specify output json file path as arguments"
				help_task
			else
				./exec.sh platform $IDX bash -c \"python /src/python/pm/technique/technique.py --action template --technique_id $3 \" > $4
				echo $4
			fi
			;;
		"create")
			if [ "$3" == "" ]; then
				echo "Please specify path to input json file as argument"
				help_task
			else
				./exec.sh platform $IDX python /src/python/pm/task/task.py --action create --config $3
			fi
			;;
		"exec")
			if [ "$3" == "" ]; then
				echo "Please specify task_id as argument"
				help_task
			else
				./exec.sh platform $IDX python /src/python/pm/task/task.py --action exec --task_id $3
			fi
			;;
		"run")
			if [ "$3" == "" ]; then
				echo "Please specify path to input json file as argument"
			else
				./exec.sh platform $IDX python /src/python/pm/task/task.py --action run --config $3
			fi
			;;
		*)
			echo "ERROR: Unrecognized task command $2"
			help_task
			;;
	esac
else
	echo "ERROR: Unrecognized command $1"
	help
fi
