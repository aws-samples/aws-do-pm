# Troubleshooting

This document contains a collection of troubleshooting tips and workarounds.

## "Error: No such container: aws-do-pm_platform_1" when running ./exec.sh or ./test.sh
This error could happen when running aws-do-pm on Docker Desktop and the configured version of docker-compose does not match the running version on your system. To resolve the error, execute `docker-compose --version` to find out if you are running compose v1 or v2. Then execute `./config.sh` and ensure `DOCKER_COMPOSE_VERSION` is set correctly.

## "error: timed out waiting for the condition" when running demo scripts on Kubernetes
Such errors could happen when Kubernetes does not have enough resources or pods take too long to come up. Try increasing the number of nodes in your cluster.