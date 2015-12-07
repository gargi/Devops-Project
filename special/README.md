# Special Milestone
We have implemented 2 components as part of special milestone.

1. Auto Scaling Docker Deployment
=================================
The infrastructure/proxy server node monitors the request per seconds for the deployed application. Based on the request per second threshold the infrastructure module will trigger autoscaling.
The Redis container on infrastructure node is used to store the instance count and IP:port of the production containers.

![](https://raw.githubusercontent.com/gsrajadh/Devops-Project/master/special/Screenshots/Screen%20Shot%202015-12-06%20at%2010.58.30%20PM.png)

Scale Up
--------
If the request per second goes above the threshold then Scale Up procedure is initiated. The new container instance called production#{instance count} is started using anisble playbook [scale_up.yml](scale_up.yml).
The scale up procedure has following states:

1. IDLE: Initial state

2. BUSY: When Scale up procedure is initiated. Ansible playbook is invoked to start a new container for production and register a callback for container to be ready.

3. READY: Moves to READY state when callback is called and new container is UP. The instance count is incremented and containers IP:port information is updated in Redis. This allows proxy server to distribute traffic to the new container.

4. UP: In this state the infrastructure module monitors the request per seconds and accordingly further scale up or scale down procedure is initiated.

Scale Down
----------
If the request per second falls below the set threshold then scale down procedure is initiated. The container instance with id production{instance count} is stopped using ansible playbook [scale_down.yml](scale_down.yml).
The scale down procedure goes through following states:

1. UP: Initial state

2. BUSY: When scale down procedure is initiated. The instance count is decremented and ansible [playbook](scale_down.yml) is invoked. The callback is registered to track the status of scale down.

3. IDLE: Callback is invoked and marks the scale down success. Further monitors request per second to scale up or down.

#### Screencast
[Screencast for Auto Scaling Docker](https://youtu.be/CFczPKizAxw)

2. Flamegraph
=============
In this feature we have implemented functionality to generate "flamegraph" in case of application crash. We have used [Direwolf](https://github.ncsu.edu/mpancha/Direwolf) (A RoR application) to demo this feature. Flamegraph feature has been implemented in app using Ruby and the following Gems:

1. gem ['rack-mini-profiler'](https://rubygems.org/gems/rack-mini-profiler/versions/0.9.7): This is the gem on which the flamegraph gem is dependent. This is used by the Flamegraph gem to track the functional flow or requests.

2. gem ['stackprof'](https://rubygems.org/gems/stackprof/versions/0.2.7): This gem is used to get stack trace of failed request. The stack trace is then parsed to generate the flamegraph.

3. gem ['flamegraph'](https://github.com/SamSaffron/flamegraph?pp=flamegraph): The "Flamegraph" gem is actually used for constructing the flamegraph for the failed request from the parsed output of the "stackprof" gem.

![](https://raw.githubusercontent.com/gsrajadh/Devops-Project/master/special/Screenshots/Screen%20Shot%202015-12-06%20at%2010.56.30%20PM.png)

#### Screencast
[Screencast for Flamegraph](https://youtu.be/vvVSaXT9mfs)

Presentation of the entire continuous integration pipeline can be found [here](https://www.youtube.com/watch?v=Um-hNlRYMGY).
