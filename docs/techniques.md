# Techniques

Techniques are a central building block of the aws-do-pm framework. They define how to complete a task. A technique contains a task template. The task template defines the information that a task needs at runtime. In object-oriented terms, a technique is a class, and a task is an object. A technique defines the "How" and a task defines the "What" of a unit of work.

For development purposes a technique is defined as a program which runs in a `target orchestrator`, the entry point to the program is an `executor` which takes a single argument named `--config`. The argument specifies the path to a json file, which follows the `task template` registered in the technique and provides all necessary configuration for the program. 

## 1. Command line Interface
The PM CLI offers a menu of technique-related commands.

### 1.1. Help
Use the help system to learn more about the technique menu of the PM CLI.

```
./pm technique --help
```
Output:
```
Usage:
    ./pm technique <action> [arguments]

    actions:
        ls                                        - list standard config items
        describe <technique_id>                   - describe an existing technique
        template <technique_id>                   - export task template from an existing technique
        register <config_json_filepath>           - add a new technique using the provided config json path
        remove <technique_id>                     - delete an existing technique
```
### 1.2. List
List the available techniques by executing the following PM CLI command either from your shell or from the platform container (by running `./exec.sh` first):

```
./pm technique ls
```
Output:
```
000ROOTNODEID000 technique_registration_graphdb ['technique', 'register', 'graphdb'] Technnique registration using graph database.
c03623kizy06twxajbt2wgr7bs7ghumg data_registration ['data', 'register'] Import data to storage and register it in the graph database
vyeadt2bivrpfbgw66h7r8oq4f4dp1wf model_registration ['model', 'register'] Upload model and register it in the graph database
fyd77r2f504mux7lqyz16upt0ynbti9k model_build_ann ['model', 'build', 'ann'] Build model using artificial neural network
ghzrgcwia8984k57fvtza1e5sl6mud26 model_serve_grpc ['model', 'serve', 'grpc', 'service', 'deploy'] Serve a model as a gRPC service
lcm7kriknfgy9xxlyofhzhfru9g97le0 model_service_configure ['model', 'service', 'configure'] Configure the model service with an updated model
l90obo0myv0ko7iyrvq69p88p9pkn8qv model_service_destroy ['model', 'service', 'destroy'] Stop and remove a model service
phbcrp1maka7v11bdhyqx0tdvpm3h2fd model_update_ukf_grpc ['model', 'update', 'ukf', 'grpc'] Update model using Unscented Kalman Filter and gRPC
gs0efg1ggemccochnci9gvbn6436u7dz model_predict_grpc ['model', 'predict', 'grpc'] Predict with an existing model which is servced as a gRPC service
ew1lqmb6osxepmieb5ne4fs3yiz69trg model_sensitivity_grpc ['analyze', 'model', 'sensitivity', 'sobol', 'grpc'] Analyze sensitivity of model parameters and inputs of an existing model which is servced as a gRPC service
ghfiudgg2mdl6uoxkg0uf2rrpbojmgkd ev_data_select ['ev', 'data', 'select'] Select a subset of fleet EV data for a specific vehicle and route
```
This list provides all the technique ids, names, tags, and brief descriptions of the techniques that are included in the aws-do-pm project. For detailed information on each of these techniques, please see the next section in this document and follow the links to technique-specific documentation.

### 1.3. Describe
Describe a technique by copying the technique id of interest from the list above and providing it as argument to the `./pm technique describe ` command.
```
./pm technique describe c03623kizy06twxajbt2wgr7bs7ghumg
```
Output:
```
{
  "_key": "c03623kizy06twxajbt2wgr7bs7ghumg",
  "_id": "technique/c03623kizy06twxajbt2wgr7bs7ghumg",
  "_rev": "_dwkWlD6---",
  "technique_id": "c03623kizy06twxajbt2wgr7bs7ghumg",
  "created_dt": "20220224-023901-689643",
  "updated_dt": "",
  "technique_tags": [
    "data",
    "register"
  ],
  "technique_name": "data_registration",
  "technique_description": "Import data to storage and register it in the graph database",
  "node_name": "data_registration",
  "task_target_orchestrator": "python",
  "task_container_image": "aws-do-pm-platform:latest",
  "task_executor_filepath": "/src/python/pm/data/task_executor_register_data.py",
  "task_template": {
    "task_id": "<newid1>",
    "task_name": "register",
    "technique_name": "data_registration",
    "task_options": [
      "-it",
      "--rm",
      "-v",
      "<path>:/register"
    ],
    "node_name": "register",
    "created_dt": "<timestamp>",
    "analyticSettings": {
      "pm_s3_bucket": "aws-do-pm",
      "pm_root_path": "wd",
      "local_path": "<path>",
      "filename": "<main_file>",
      "rel_dest_path": "data/<newid2>",
      "description": "Registered dataset"
    },
    "inputs": {},
    "outputs": {},
    "input_artifacts": {},
    "output_artifacts": {
      "data": [
        "<newid2>"
      ]
    },
    "savedState": {},
    "status": ""
  }
}
```
This template shows that the `data_registration` technique is embedded in the `aws-do-pm-platform` container and is executed by the `/src/python/pm/data/task_executor_register_data.py` script using `python`. The task configuration parameters are specified in the `task_template`. The `technique_tags` specify key words by which this technique can be found when searched within aws-do-pm. 

### 1.4. Go
To allow flexibility when extending [aws-do-pm](https://github.com/aws-samples/aws-do-pm) with new techniques, the PM CLI implements a menu system that is driven by tags. Since the tags for the data registration technique we described above are "data" and "register", a template for a data registration task can be generated by the CLI by specifying either of these two commands:
```
./pm go data register
```
or
```
./pm go register data
```
Output:
```
{
  "task_id": "uh3ojc1ldc4yje9a7d22qjc6gzvs0z34",
  "task_name": "register",
  "technique_name": "data_registration",
  "task_options": [
    "-it",
    "--rm"
  ],
  "node_name": "register",
  "created_dt": "20220225-200618-911199",
  "analyticSettings": {
    "pm_s3_bucket": "aws-do-pm",
    "pm_root_path": "wd",
    "local_path": "<path>",
    "filename": "<main_file>",
    "rel_dest_path": "data/yece750htvz4m2pg2n6vpjeaaspt8e7e",
    "description": "Registered dataset"
  },
  "inputs": {},
  "outputs": {},
  "input_artifacts": {},
  "output_artifacts": {
    "data": [
      "yece750htvz4m2pg2n6vpjeaaspt8e7e"
    ]
  },
  "savedState": {},
  "status": ""
}
```
The task template is automatically saved to `wd/tmp/1/input.json`. The user can edit the file to specify any of the task-specific values that are enclosed in `<>`, then execute the task by using the `./pm do <path>` command.

### 1.5. Do
The `do` command of the PM CLI allows a user to create and execute any task based on a provided input json file. All tasks in [aws-do-pm](http://github.com/aws-samples/aws-do-pm) can be accomplished, by only using the `./pm go` and `./pm do` commands.

While running the `ev-demo` script, a generated training dataset is saved in `wd/generated_ev_data/train_data`. We will use that to demonstrate the `./pm do` command.

Edit file `wd/tmp/1/input.json` which was created in the previous step and replace:
*  `<path>` with `wd/generated_ev_data/train_data`
*  `<main_file>` with `input_output.json`. Then run the `do` command below:

```
./pm do wd/tmp/1/input.json
```
Output:
```
task/vivkgv7m0rj163zzp53trhkemkx1mxpt
Executing task from wd/task/vivkgv7m0rj163zzp53trhkemkx1mxpt/task.json ...
Executing PM task:
['python', '/src/python/pm/data/task_executor_register_data.py', '--config', 'wd/task/vivkgv7m0rj163zzp53trhkemkx1mxpt/task.json']
data/pfafcru5lhchn6azqzjmtp1m7u7gmznb
Return code: 0
upload: wd/generated_ev_data/train_data/input_output.json to s3://aws-do-pm/data/pfafcru5lhchn6azqzjmtp1m7u7gmznb/input_output.json
download: s3://aws-do-pm-alex/data/pfafcru5lhchn6azqzjmtp1m7u7gmznb/input_output.json to wd/data/pfafcru5lhchn6azqzjmtp1m7u7gmznb/input_output.json
upload: wd/data/pfafcru5lhchn6azqzjmtp1m7u7gmznb/metadata.json to s3://aws-do-pm/data/pfafcru5lhchn6azqzjmtp1m7u7gmznb/metadata.json
```

## 2. Technique details
The project comes with a set of core techniques that can be used as building blocks for a predictive modeling application. The framework is also extensible, through registeration of user-defined custom techniques, like ev-data-generation.

### 2.1. System techniques

#### 2.1.1. technique_registration
Registering a technique is in itself a technique. The initialization of the system starts by creating the technique_registration technique and that becomes the root node in the system graph. 

To register a technique, a registration json file is required. Examples of registration files are available in [../src/python/pm/technique](../src/python/pm/technique) and [../src/python/example/ev/technique/ev_data_select](../src/python/example/ev/technique/ev_data_select/).
The data_registration technique was created by executing task [../src/python/pm/task/task_technique_register_data_registration.json](../src/python/pm/task/task_technique_register_data_registration.json) which points to the registration json [../src/python/pm/technique/technique_registration_data_registration.json](../src/python/pm/technique/technique_registration_data_registration.json)

If you would like to register your own custom technique, create a technique_registration.json using one of the available examples, then execute `./pm technique register <path_to_technique_registration.json>`.

#### 2.1.2. data_registration
The data registration technique allows users of aws-do-pm to import datasets into the system. The imported dataset is given a unique id and uploaded to the S3 bucket as well as temporarily stored in the platform shared volume. Metadata about the dataset is generated and stored in the same locations as well as the graph database.

To register your own dataset, use the following PM CLI command:
```
./pm data register <local_path> <main_file> ["dataset description"]
```
* `local_path` can be a relative or absolute path to the folder containing your dataset
* `main_file` is the name of the main file that contains data in the folder
* `"dataset description"` is a free-form text description of your data. Please enclose the description in double quotes on the command line to ensure that the entire description is passed to the CLI as a single argument.

#### 2.1.3. model_registration
Model registration allows users to import models that have been built outside of aws-do-pm. To register an external model, use `./pm model register <folder_path> <model_filename> ["model description"]`.
>Note: if specifying model description, please ensure it is enclosed in double quotes so the entire description is submitted as a single argument.

#### 2.1.4. model_build_ann
To build an Artificial Neural Network (ANN) model use the following command:
`./pm model build <data_id>`. 
Detailed documentation of this technique is available here: [../src/python/technique/model_build_ann/README.md](../src/python/technique/model_build_ann/README.md)

#### 2.1.5. model_serve_grpc
To deploy a model as a gRPC service, use the following command:
`./pm service deploy <model_id>`. 
Detailed documentation of this technique is available here: [../src/python/technique/model_serve_grpc/README.md](../src/python/technique/model_serve_grpc/README.md)

#### 2.1.6. model_service_configure
To update a model service with a new model, use the following command:
`./pm service configure <service_id> <model_id>`, where `service_id` is the id of the service to configure, and `model_id` is the new model that the service should be configured with.

#### 2.1.7. model_service_destroy
To decommission a model service, use the following command:
`./pm service destroy <service_id>`. This command removes the model service and deletes its corresponding pod.

#### 2.1.8. model_predict_grpc
To generate a prediction using a specific model and data, use the following command:
`./pm model predict <model_id|service_id> <data_id>`. 
If a `service_id` is specified, it will be used to generate a prediction. If `model_id` is specified, the model will be deployed as a service, the prediction will be made, and then the service will automatically be destroyed. Detailed information about the model prediction technique is available here: [../src/python/technique/model_predict_grpc/README.md](../src/python/technique/model_predict_grpc/README.md)

#### 2.1.9. model_update_ukf
To update a model using specific data, use the following command:
`./pm model update <model_id|service_id> <data_id>`. If a service_id is specified, it will be used to update the model, if model_id is specified, a service will be created and automatically destroyed when the model update is done. Detailed documentation about the UKF model update technique is available here: [../src/python/technique/model_update_ukf_grpc/README.md](../src/python/technique/model_update_ukf_grpc/README.md)

#### 2.1.10. model_sensitivity_grpc
To run sensitivity analysis of a model, use the following command:
`./pm model sensitivity <model_id|service_id> <data_id>`. If a service_id is specified, the analysis will be run against it. If model_id is specified, a service will be created and automatically destroyed when the sensitivity analysis is done. Detailed documentation about this technique is available here: [../src/python/technique/model_sensitivity_grpc/README.md](../src/python/technique/model_sensitivity_grpc/README.md)

### 2.2. Custom technique example
#### 2.2.1. ev_data_select
The ev_data_select technique is a custom technique, specific to the EV use case. It does not come pre-registered in aws-do-pm. We register this technique, using `./pm technique register <config_json_filepath>` in the demo scripts. The data selection technique is needed for the EV use case so we may simulate data for a particular vehicle and route arriving from the field. In reality this data is selected and extracted from the raw dataset and saved with its own data id. Detailed documentation about this technique is available here: [../src/python/example/ev/technique/ev_data_select/README.md](../src/python/example/ev/technique/ev_data_select/README.md).

#### 2.2.2. ev_datagen_em
The ev_datagen_em code is structured as a technique, but is not registered with aws-do-pm as part of the demo. This is to showcase how code running outside of aws-do-pm can be used in parallel with aws-do-pm techniques and tasks. We generate the data by running this code in a Docker container, then register the raw dataset with aws-do-pm. Detailed documentation about the EV data generation code is available here: [../src/python/example/ev/technique/ev_datagen_em/README.md](../src/python/example/ev/technique/ev_datagen_em/README.md)

<br/>
<br/>

Back to main [README.md](../README.md)
