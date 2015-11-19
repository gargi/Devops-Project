#!/bin/sh
echo "Building docker image"
docker -H 52.33.241.189:4243 build -t direwolf:$1 /var/jenkins_home/jobs/$2/workspace/
docker -H 52.33.241.189:4243 rmi localhost:5000/direwolf:$1
docker -H 52.33.241.189:4243 tag direwolf:$1 localhost:5000/direwolf:$1
docker -H 52.33.241.189:4243 push localhost:5000/direwolf:$1
ansible-playbook -i inventory_$1 "$1".yml
exit 0
