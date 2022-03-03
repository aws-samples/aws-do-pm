# Deployment of aws-do-pm to EKS

## 1. Create an EKS Cluster using the aws-do-eks project

Below we detail the steps the user has to follow to create an [Amazon EKS](https://aws.amazon.com/eks/) cluster. We recommend using an [EC2 Instance](https://aws.amazon.com/ec2/) or [AWS Cloud9](https://aws.amazon.com/cloud9/) to execute the scripts. The same terminal can also be used to interact with the cluster.

### 1.1. Clone aws-do-eks
```
git clone https://github.com/aws-samples/aws-do-eks
```
Follow through the instructions in the README.md of [https://github.com/aws-samples/aws-do-eks](https://github.com/aws-samples/aws-do-eks) to setup your EKS cluster. We have listed some representative configuration values below:

### 1.2. Configure cluster
Edit the configuration file `wd/conf/eks.conf`.
  * Check the name, region and availability zones for the cluster  
  * Set your VPC CIDR Block to the range of addresses that does not collide with other VPC CIDRs in your account for the selected region.
    ```
    export CLUSTER_VPC_CIDR=172.32.0.0/16     
    ```
  * Set the instance type for system node group. Default: c5.2xlarge
  * Set the node group instance types and sizes for the worker nodes in the cluster. The specifications are done for the CPU, GPU and Inf1 Nodes. 
  ```
  CPU_NODEGROUP_INSTANCE_TYPES=(c5.4xlarge)
  CPU_NODEGROUP_SIZES=(1)
  ```
  For a mix of instances as node groups, you can specify a space separated list, following the example below:
  ```
  CPU_NODEGROUP_INSTANCE_TYPES=(c5.4xlarge m5.8xlarge)
  CPU_NODEGROUP_SIZES=(1 1)
  ```
### 1.3. Build aws-do-eks container, run it, and open a command shell
To build, run, and open a shell into the aws-do-eks container, execute the following commands:
  ```
  ./build.sh
  ./run.sh
  ./exec.sh
  ```
### 1.4. Run eks-create.sh script
Create the EKS cluster by running the `./eks-create.sh` script. This script automatically runs a CloudFormation process that will take around 20 - 30 minutes to finish provisioning all infrastructure including a VPC with the specified CIDR, subnets, NAT Gateway, and the EKS cluster.
  ```
  ./eks_create.sh
  ```
### 1.5. Verify cluster status
Once the create script has finished, we can query the status of the EKS cluster through
  ```
  ./eks_status.sh
  ```
A sample eks_status log is shown below for reference:

  ```
  root@8b5645a5ff6b:/eks# ./eks-status.sh 
  Status of cluster do-eks ...
  
  eksctl get cluster --name do-eks
  2022-02-03 02:20:51 [ℹ]  eksctl version 0.66.0
  2022-02-03 02:20:51 [ℹ]  using region us-east-1
  NAME    VERSION    STATUS    CREATED            VPC            SUBNETS                                    SECURITYGROUPS
  do-eks    1.21    ACTIVE    2022-02-03T01:33:30Z    vpc-0fc65db3a231269b9    subnet-0057cfaab42ef69ba,subnet-015ea5f0056972292,subnet-07dbc80565309801a,subnet-0cd831a95bac36775,subnet-0d67a59c8ebe44b20,subnet-0eb5080babdf0f7c4,subnet-0f76fc8f0c6a0a1ba,subnet-0fbef9adc2b00ed85    sg-0b2aa6af97c65f84e
  
  eksctl get nodegroups --cluster do-eks
  2022-02-03 02:20:51 [ℹ]  eksctl version 0.66.0
  2022-02-03 02:20:51 [ℹ]  using region us-east-1
  CLUSTER    NODEGROUP    STATUS    CREATED            MIN SIZE    MAX SIZE    DESIRED CAPACITY    INSTANCE TYPE    IMAGE ID    ASG NAME
  do-eks    c5-4xlarge    ACTIVE    2022-02-03T01:56:33Z    0        10        1            c5.4xlarge    AL2_x86_64eks-c5-4xlarge-10bf5ea6-12dd-fa16-fb54-986416d111bc
  do-eks    g4dn-4xlarge    ACTIVE    2022-02-03T01:59:56Z    0        10        1            g4dn.4xlarge    AL2_x86_64_GPU    eks-g4dn-4xlarge-86bf5ea7-9e09-2023-7896-e741a37c7112
  do-eks    inf1-2xlarge    ACTIVE    2022-02-03T02:03:53Z    0        10        0            inf1.2xlarge    AL2_x86_64_GPU    eks-inf1-2xlarge-30bf5ea9-6d7a-b898-1764-1f46e0622717
  do-eks    system        ACTIVE    2022-02-03T01:51:27Z    1        10        1            c5.2xlarge    AL2_x86_64eks-system-7abf5ea3-bcc7-c19b-63a7-2a0369cdc158
  
  ```

>Note: If the `./eks-create.sh` script has errors, it can be executed again. Doing that may help create resources that failed during the initial run.

### 1.6. Create a kube config file
The next critical step is to create a kube config file. This file will be copied to the ~/.kube folder so that any kubectl commands will be able to interact with the EKS cluster.
From within the `aws-do-eks` shell, navigate to directory `ops/setup/kubeconfig` and execute the `./run.sh` script.
```
cd ops/setup/kubeconfig
./run.sh
```  
The kube config credentials are created in the temporary folder (/tmp/kube/k8s-sa-admin-kube-system-conf)

Test the kubeconfig by using it to list all pods in the EKS cluster.
```
KUBECONFIG=/tmp/kube/k8s-sa-admin-kube-system-conf kubectl get pods -A
```

After verifying the kube config, explicitly move it into the `~/.kube` folder.

```
root@8b5645a5ff6b:/eks# mv ~/.kube/config ~/.kube/config_old
root@8b5645a5ff6b:/eks# cp /tmp/kube/k8s-sa-admin-kube-system-conf ~/.kube/config
```

## 2. Deploy system packages to cluster
The following system packages need to be deployed to the cluster as they will be needed by aws-do-pm
### 2.1. Load Balancer Controller
The Load Balancer controller deployment scripts are present within the `aws-do-eks` shell in folder `deployment/aws-load-balancer-controller`. 
```
cd /deployment/aws-load-balancer-controller
./deploy-aws-load-balancer-controller.sh
```

### 2.2. EFS

#### 2.2.1. Create EFS Volume
Create an EFS volume so that we can set up a shared file system, accessible by all pods.

Navigate to directory `eks/deployment/efs-csi`
```
cd eks/deployment/efs-csi
```
  
Get the name of the cluster:
```
aws eks list-clusters
```

Then edit file `efs-create.sh` and verify that the `CLUSTER_NAME` is set to the same as the cluster you just created.
```
CLUSTER_NAME=do-eks
```

Next, execute the script:
```
./efs-create.sh
```
This script will use the AWS CLI to provision an EFS volume accessible from your EKS cluster.

#### 2.2.2. Deploy EFS CSI Plugin
To deploy the EFS CSI plugin, run the `./deploy.sh` script. 
```
./deploy.sh
```

Verify the deployment by getting the list of running pods. Check if the efs_csi_controller pod exists and is in Running state.
Check if an efs-csi-node pod exists for each node in the cluster. A successful deployment for a two-node cluster has a log like the one below:
```
root@8b5645a5ff6b:/eks/deployment/efs-csi# k get pods
NAME                                   READY   STATUS    RESTARTS   AGE
aws-node-dtnl8                         1/1     Running   0          73m
aws-node-fdz2b                         1/1     Running   0          64m
cluster-autoscaler-6947b58b46-nbdmv    1/1     Running   0          14m
coredns-66cb55d4f4-2m44q               1/1     Running   0          83m
coredns-66cb55d4f4-hjt8f               1/1     Running   0          83m
efs-csi-controller-5964b9c55b-98fh4    3/3     Running   0          60s
efs-csi-controller-5964b9c55b-hw7n5    3/3     Running   0          60s
efs-csi-node-hnn57                     3/3     Running   0          60s
efs-csi-node-kjwdb                     3/3     Running   0          60s
efs-share-test                         1/1     Running   0          29s
kube-proxy-jbkdw                       1/1     Running   0          73m
kube-proxy-vhnw7                       1/1     Running   0          64m
nvidia-device-plugin-daemonset-c52dm   1/1     Running   0          63m
nvidia-device-plugin-daemonset-v2nfb   1/1     Running   0          63m
root@8b5645a5ff6b:/eks/deployment/efs-csi# 
```

### 2.3. Deploy the nvidia-device-plugin (Optional)
If you have GPU nodes in the cluster, verify if the nvidia-device-plugin is installed by running the following command:

```
kubectl get daemonset -A
```
If the `nvidia-device-plugin-daemonset` is present, then no further action is necessary, otherwise deploy the `nvidia-device-plugin` by navigating to directory `deployment/nvidia-device-plugin` and executing the `./deploy.sh` script.
```
cd deployment/nvidia-device-plugin
./deploy.sh
```

# 3. Deploy aws-do-pm 

## 3.1. Create and set default namespace
By default, the namespace in EKS is kube-system. Create namespace `aws-do-pm` and set it as default by using the `kubens` utility:
```
kubectl create ns aws-do-pm
kn aws-do-pm
```

## 3.2. Clone the aws-do-pm project
```
git clone https://github.com/aws-samples/aws-do-pm
```

## 3.3. Configure 
Setup the configuration parameters for aws-do-pm by executing `./pm config set`, values shown below are for reference
```
ubuntu@ip-172-31-9-117:~/aws-do-pm$ ./pm config show

Current configuration:
    AWS_ACCESS_KEY_ID: ***
    AWS_SECRET_ACCESS_KEY: ***
    REGION: us-east-1
    REGISTRY: ******.dkr.ecr.us-east-1.amazonaws.com/
    BUILD_TO: docker
    PM_TO: kubernetes
    PROCESSOR: cpu
    PM_S3_BUCKET: ***
    PM_PLATFORM_SCALE: 1
    PM_GRAPHDB_SYSTEM_CR: root
    PM_GRAPHDB_ID: pm
    PM_GRAPHDB_CR: pm
    EFS_VOLUME_ID: ******* [Find the efs volume from console (or) deployment/efs-csi/efs-pvc.yaml]
    ALB_ALLOW_CIDRS: 0.0.0.0/0 [Can be restricted to private IP's]
    (or)
    ALB_ALLOW_CIDRS: 44.193.5.225/32 [get your ip from `curl icanhazip.com`]
    KCFG_ENC: [Leave at default, replaced by the value of encoded key]
```

## 3.4. Build
Build all containers by executing `./build.sh all`
```
./build.sh all
```

## 3.5. Push 
The following commands authenticate with Amazon ECR, create the necessary repositories, and push all container images:
```
./login.sh
./ecr-setup.sh
./push.sh all
```

It takes around 20 minutes to push all containers into ECR

## 3.6. Run
Execute the run script to deploy the aws-do-pm services to the cluster.
```
./run.sh
```

## 3.7. Verify
Verify successful deployment by executing the `./status.sh` script.
You should be able to see three pods running: graphdb, platform, and ui.
```
./status.sh
Showing status on target orchestrator kubernetes ...
NAME                        READY   STATUS    RESTARTS   AGE
graphdb-74b77d866-2djhj     1/1     Running   0          2m12s
platform-5c4f55f97f-hvb6p   1/1     Running   0          2m12s
ui-69b78dffdc-mln4d         1/1     Running   0          2m12s
```

# 4. Use aws-do-pm 

## 4.1. Open a platform shell
Open a shell into the platform pod by running the `./exec.sh` script.
```
./exec.sh
```

## 4.2. Configure the platform
Execute `./pm config set` to review and set the platform configuration

## 4.3. Browse
Verify that the load balancers have been provisioned and the controller service endpoints have an available address:
```
root@8b5645a5ff6b:kubectl get ingress
NAME       CLASS    HOSTS   ADDRESS                                                                  PORTS   AGE
graphdb    <none>   *       k8s-awsdopm-graphdb-437e4f937e-802609209.us-east-1.elb.amazonaws.com     80      51m
platform   <none>   *       k8s-awsdopm-platform-01d752bb5e-1644131234.us-east-1.elb.amazonaws.com   80      51m
```

## 4.4. Run EV demos
You have successfully deployed [aws-do-pm](https://github.com/aws-samples/aws-do-pm) to EKS.
At this point you can use the `pm` CLI commands to try the capabilities of the platform or run the EV demo scripts.

```
./ev-demo
```
or
```
./ev-fleet-demo
```

## 5. Bonus Tips
Execute the following commands from your aws-do-eks shell.

### 5.1. View list of nodes and node types in the cluster
```
cd ops
./nodes-list.sh
./nodes-types-list.sh
```

### 5.2. View node utilization
```
watch "kubectl top node"
```

### 5.3. Login to a node
Get a list of nodes and select the name of the node you'd like to login to.
```
k get no
```
Then exec into the running node using `kubeshell`:
```
ks <node_name>
```

<br/>
<br/>

Back to main [README.md](../README.md)
