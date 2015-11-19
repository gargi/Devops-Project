#!/usr/bin/python
import os
import sys
import boto.ec2
#import subprocess
from subprocess import Popen, PIPE, STDOUT
import ansible.runner
import redis

from ansible.inventory import Inventory
from ansible.playbook import PlayBook
from ansible import utils
from ansible import callbacks
#import digitalocean
import time
import webbrowser

class deployment:
   """Deployment class """
   def __init__(self):
      self.aws_con=''
      self.aws_image = 'ami-d05e75b8'
      self.aws_size = 't2.micro'
      
   def create_aws_instance(self):
      ''' use access key and '''
      self.aws_con = boto.ec2.connect_to_region("us-east-1")
      self.aws_con.run_instances(self.aws_image,key_name='devops',instance_type=self.aws_size, security_groups=['hw1'])

   def destroy_aws_instance(self):
      self.con = boto.ec2.connect_to_region("us-east-1")
      reservations = self.con.get_all_reservations()
      for res in reservations:
         for instance in res.instances:
            instance.terminate()
            #print "instance terminated"

   def get_aws_reservation(self):
      con = boto.ec2.connect_to_region("us-east-1")
      reservations = con.get_all_reservations()
      inst = []
      #print reservations
      for res in reservations:
         #print res
         for instance in res.instances:
            #print instance
            #print instance.state
            if instance.state == "running":
                inst.append(instance.ip_address)
      return inst

def aws(phase):
   #parse args
   with open("keys/rootkey.csv","r") as keyfile:
      lines = keyfile.readlines()
      aws_access_key = lines[0].split('=')[1].strip(' ').rstrip()
      aws_secret_key = lines[1].split('=')[1].strip(' ').rstrip()

   os.environ['AWS_ACCESS_KEY_ID']= aws_access_key
   os.environ['AWS_SECRET_ACCESS_KEY']= aws_secret_key
   
   d = deployment()
   red = redis.StrictRedis(host='localhost', port=6379, db=0)
   if phase == 0:
      print "Clean up stale reservations...*****************\n"
      d.destroy_aws_instance()
   if phase == 1:
      d.create_aws_instance()
      d.create_aws_instance()
      print "\nCheck AWS instance status...******************"
      aws_ip = d.get_aws_reservation()
      while aws_ip == None or len(aws_ip) < 2:
         print "AWS Instance not ready, retry after 30 sec"
         time.sleep(30)
         aws_ip = d.get_aws_reservation()
      canary = aws_ip[0]
      production = aws_ip[1]
      print "AWS Canary Instance =" + canary
      print "AWS Production Instance =" + production
      print "Update Redis"
      red.set('canary',"http://"+canary+":3000")
      red.set('production', "http://"+production+":3000")
      print red.get('canary')
      print red.get('production')
      print "\nWriting Inventory...**************************"
      aws_inv_can = "canary ansible_ssh_host="+canary+" ansible_ssh_user=ubuntu ansible_ssh_private_key_file=./keys/devops.pem\n"
      with open("inventory_canary","w") as f:
         f.write(aws_inv_can)
      aws_inv_prod = "production ansible_ssh_host="+production+" ansible_ssh_user=ubuntu ansible_ssh_private_key_file=./keys/devops.pem\n"
      with open("inventory_production","w") as f:
         f.write(aws_inv_prod)
      with open("inventory", "w") as f:
         f.write(aws_inv_can+"\n")
         f.write(aws_inv_prod)
   if phase == 2:
      os.environ['ANSIBLE_HOST_KEY_CHECKING']="false"
      utils.VERBOSITY = 0
      playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
      stats = callbacks.AggregateStats()
      runner_cb = callbacks.PlaybookRunnerCallbacks(stats, verbose=utils.VERBOSITY)
      inventory = Inventory('inventory')
      print "\nRun Ansible PlayBook...**********************"
      pb = PlayBook(playbook='server_play.yml',
              inventory=inventory,
              callbacks=playbook_cb,
              runner_callbacks=runner_cb,
              stats=stats
           )
      pb.run()	

# Calls node js to run load balancer and web hook
def monitor():
    #red = redis.StrictRedis(host='localhost', port=6379, db=0)
    #red.set('canary',"http://52.91.89.147:3000")
    #print "Get Canary from redis"
    #print red.get('canary')
    #subprocess.check_output(["/usr/bin/nodejs", "main.js"])
    print "Starting main.js"
    p = Popen(["/usr/bin/nodejs", "main.js"], stdout = PIPE, 
        stderr = PIPE)
    for line in iter(p.stdout.readline, ''):
       print line
    rc = p.wait()
    p.stdout.close()

def main(argv):
  
   if len(argv)> 1 and argv[1] == "clean":
      aws(phase=0)
   elif len(argv)>1 and argv[1] == "monitor":
      monitor()
   else:
      aws(phase=1)
      time.sleep(40)
      aws(phase=2)
      monitor()

if __name__=="__main__":
   main(sys.argv)
