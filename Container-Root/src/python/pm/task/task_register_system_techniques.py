######################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. #
# SPDX-License-Identifier: MIT-0                                     #
######################################################################

# Register embedded techniques
import pm.task.task as task

if __name__ == '__main__':
    
    #import debugpy; debugpy.listen(('0.0.0.0',5678)); debugpy.wait_for_client(); breakpoint()

    # Print new line
    print("")

    # data_registration
    print("Registering technique data_registration ...")
    registration_task_json_filepath = '/src/python/pm/task/task_technique_register_data_registration.json'
    task.create_task(registration_task_json_filepath, execute=True)

    # model_registration
    print("Registering technique model_registration ...")
    registration_task_json_filepath = '/src/python/pm/task/task_technique_register_model_registration.json'
    task.create_task(registration_task_json_filepath, execute=True)

    # model_build_ann
    print("Registering technique model_build_ann ...")
    registration_task_json_filepath = '/src/python/pm/task/task_technique_register_model_build_ann.json'
    task.create_task(registration_task_json_filepath, execute=True)

    # model_serve_grpc
    print("Registering technique model_serve_grpc ...")
    registration_task_json_filepath = '/src/python/pm/task/task_technique_register_model_serve_grpc.json'
    task.create_task(registration_task_json_filepath, execute=True)

    # model_service_configure
    print("Registering technique model_service_configure ...")
    registration_task_json_filepath = '/src/python/pm/task/task_technique_register_model_service_configure.json'
    task.create_task(registration_task_json_filepath, execute=True)
    
    # model_service_destroy
    print("Registering technique model_service_destroy ...")
    registration_task_json_filepath = '/src/python/pm/task/task_technique_register_model_service_destroy.json'
    task.create_task(registration_task_json_filepath, execute=True)

    # model_update_ukf
    print("Registering technique model_update_ukf_grpc ...")
    registration_task_json_filepath = '/src/python/pm/task/task_technique_register_model_update_ukf_grpc.json'
    task.create_task(registration_task_json_filepath, execute=True)

    # model_predict_grpc
    print("Registering technique model_predict_grpc ...")
    registration_task_json_filepath = '/src/python/pm/task/task_technique_register_model_predict_grpc.json'
    task.create_task(registration_task_json_filepath, execute=True)

    # model_sensitivity_grpc
    print("Registering technique model_sensitivity_grpc ...")
    registration_task_json_filepath = '/src/python/pm/task/task_technique_register_model_sensitivity_grpc.json'
    task.create_task(registration_task_json_filepath, execute=True)




