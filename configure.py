#!/usr/bin/python
import os
import sys
import boto.ec2
import subprocess
import ansible.runner
from ansible.inventory import Inventory
from ansible.playbook import PlayBook
from ansible import utils
from ansible import callbacks
#import digitalocean
import time
import webbrowser

class deployment:
   """Deployment class """
   def __init__(self, d_token):
      self.aws_con=''
      self.aws_image = 'ami-d05e75b8'
      self.aws_size = 't2.micro'
      
   def create_aws_instance(self):
      ''' use access key and '''
      self.aws_con = boto.ec2.connect_to_region("us-east-1")
      self.aws_con.run_instances(self.aws_image,key_name='aws_hw1',instance_type=self.aws_size, security_groups=['hw1'])

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
      #print reservations
      for res in reservations:
         #print res
         for instance in res.instances:
            #print instance
            #print instance.state
            if instance.state == "running":
               return instance.ip_address
      return None

def main(argv):
   #parse args
   phase = 0
   if len(argv)!=2:
      exit(1)
   if argv[1]=="clean":
      phase = 0
   elif argv[1] == "inventory":
      phase = 1
   elif argv[1] == "deploy":
      phase = 2
   with open("keys/rootkey.csv","r") as keyfile:
      lines = keyfile.readlines()

      aws_access_key = lines[0].split('=')[1].strip(' ').rstrip()
      aws_secret_key = lines[1].split('=')[1].strip(' ').rstrip()

   os.environ['AWS_ACCESS_KEY_ID']= aws_access_key
   os.environ['AWS_SECRET_ACCESS_KEY']= aws_secret_key
   
   if phase == 0 or phase == 1:
      d = deployment(d_token)
      print "Clean up stale reservations...*****************\n"
      d.destroy_aws_instance()
      d.destroy_digital_instance()
   if phase == 1:
      print "\nCheck AWS instance status...******************"
      aws_ip = d.get_aws_reservation()
      while aws_ip == None:
         print "AWS Instance not ready, retry after 30 sec"
         time.sleep(30)
         aws_ip = d.get_aws_reservation()
      print "AWS instance IP =" + aws_ip
      aws_inv = "aws ansible_ssh_host="+aws_ip+" ansible_ssh_user=ubuntu ansible_ssh_private_key_file=./keys/aws_hw1.key"
   
      print "\nWriting Inventory...**************************"
      with open("inventory","w") as f:
         f.write(aws_inv)

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
      print "\nOpening web browser...***********************"
      for host in inventory.get_hosts():
          print "Opening nginx page on ", host.name,  host.vars['ansible_ssh_host']
          webbrowser.open_new("http://"+host.vars['ansible_ssh_host'])
          time.sleep(1)

if __name__=="__main__":
   main(sys.argv)
