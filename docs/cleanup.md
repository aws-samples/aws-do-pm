# Cleanup
This document describes how to remove all resources used by [aws-do-pm](https://github.com/aws-samples/aws-do-pm).

## 1. Data
To remove all of the data that aws-do-pm created and release storage resources, open a shell into a platform container and execute `./pm system clear`.
```
./exec.sh platform 1
./pm system clear
```
> Note: If a large amount of data was stored, the cleanup operation may take a while. To accelerate data cleanup, you may manually delete the contents of the configured S3 bucket, as well as open a shell into a platform container and execute `rm -rf wd/task/* wd/data/* wd/model/* wd/tmp/*`.

## 2. Services
To remove the deployed services, simply execute the `./stop.sh` script. 
```
./stop.sh
```
Docker Compose output:
```
Stopping container aws-do-pm-platform-compose on compose ...
Stopping aws-do-pm_graphdb_1  ... done
Stopping aws-do-pm_ui_1       ... done
Stopping aws-do-pm_platform_1 ... done
Removing aws-do-pm_graphdb_1  ... done
Removing aws-do-pm_ui_1       ... done
Removing aws-do-pm_platform_1 ... done
Removing network aws-do-pm_default 
```
Kubernetes output:
```
Stopping container aws-do-pm-platform-kubernetes on kubernetes ...
namespace "aws-do-pm" deleted
persistentvolume "pm-efs-pv" deleted
persistentvolume "pm-efs-wd-pv" deleted
persistentvolume "pm-efs-graphdb-pv" deleted
persistentvolumeclaim "pm-efs-pvc" deleted
persistentvolumeclaim "pm-efs-wd-pvc" deleted
persistentvolumeclaim "pm-efs-graphdb-pvc" deleted
persistentvolume "pm-efs-pv" deleted
persistentvolume "pm-efs-wd-pv" deleted
persistentvolume "pm-efs-graphdb-pv" deleted
persistentvolumeclaim "pm-efs-pvc" deleted
persistentvolumeclaim "pm-efs-wd-pvc" deleted
persistentvolumeclaim "pm-efs-graphdb-pvc" deleted
secret "ecr-login-cred" deleted
cronjob.batch "ecr-login" deleted
serviceaccount "sa-ecr-login" deleted
role.rbac.authorization.k8s.io "role-full-access-to-secrets" deleted
rolebinding.rbac.authorization.k8s.io "ecr-login-role-binding" deleted
deployment.apps "graphdb" deleted
deployment.apps "platform" deleted
deployment.apps "ui" deleted
service "graphdb" deleted
service "ui" deleted
ingress.networking.k8s.io "graphdb" deleted
ingress.networking.k8s.io "ui" deleted
```

<br/>
<br/>

Back to main [README.md](../README.md)
