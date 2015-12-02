# Special Milestone
We have implemented 2 components as part of special milestone.

1. Auto Scaling Docker Deployment
----------------------------------
The infrastructure/proxy server node monitors the request per seconds for the deployed application. Based on the request per second threshold the infrastructure module will trigger autoscaling.
The Redis container is on infrastructure node is used to store the instance count and IP:port of the production containers.

* Scale Up
----------
If the request per second goes above the threshold then Scale Up procedure is initiated. The new container instance called production#{instance count} is started using anisble playbook [scale_up.yml](scale_up.yml).
The scale up procedure has following states:
1. IDLE: Initial state
2. BUSY: When Scale up procedure is initiated. Ansible playbook is invoked to start a new container for production and register a callback for container to be ready.
3. READY: Moves to READY state when callback is called and new container is UP. The instance count is incremented and containers IP:port information is updated in Redis. This allows proxy server to distribute traffic to the new container.
4. UP: In this state the infrastructure module monitors the request per seconds and accordingly further scale up or scale down procedure is initiated.

* Scale Down
-----------
If the request per second falls below the set threshold then scale down procedure is initiated. The container instance with id production{instance count} is stopped using ansible playbook [scale_down.yml](scale_down.yml).
The scale down procedure goes through following states:
1. UP: Initial state
2. BUSY: When scale down procedure is initiated. The instance count is decremented and ansible [playbook](scale_down.yml) is invoked. The callback is registered to track the status of scale down.
3. IDLE: Callback is invoked and marks the scale down success. Further monitors request per second to scale up or down. 

2. Flamegraph
-------------
