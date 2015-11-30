// deployment infrastructure code
var express = require('express')
var redis = require('redis')
var bodyParser = require('body-parser')
var Ansible = require('node-ansible')
var http      = require('http');
var httpProxy = require('http-proxy');
var request = require("request");
var execSync = require('child_process').exec;
var fs = require('fs')
var pserver,infra;
var scale_limit = 1;
var scale = 'down';
var infrastructure = {
  setup: function(){
     var client = redis.createClient(6379, '127.0.0.1', {});
     var proxy   = httpProxy.createProxyServer({});
     var count = 0;
     var app = express()
     var reload_production = new Ansible.Playbook().playbook('production').inventory('inventory_production');
     var reload_canary = new Ansible.Playbook().playbook('canary').inventory('inventory_canary');
     var prod_only = true;//false;
     var rps = 0;
     // Process POST from webhooks to deploy to production
     app.use(bodyParser.json())
     app.use(bodyParser.urlencoded({ extended: true }))
     app.post('/alert',function(req,res){
        console.log('alert recieved... Cut off canary traffic');
        prod_only = true;
        res.status(204).end()
       });
     app.post('/job/release/build',function(req, res){
        if(req.body && req.body.ref) {
          if(req.body.ref.indexOf('release') > -1) {
             console.log('Trigger Build process for release (check jenkins)')
             request("http://52.33.84.211:8080/job/release/build", function(error, response, body){});
          }
        }
        res.status(204).end()
     });
     app.post('/deploy', function(req, res){
        console.log('/deploy called for ref')
        console.log(req.body.ref) // form fields
        if(req.body && req.body.ref) {
          if(req.body.ref.indexOf('release') > -1) {
             console.log('deploying production (release)')
             deployProcess = execSync('./deploy.sh production release');
             deployProcess.stdout.on('data', function(data){
               console.log(data);
             })
             deployProcess.stdout.on('exit', function(data){
               console.log('deploy exited with code'+code);
             })
          };
          if(req.body.ref.indexOf('dev') > -1) {
             console.log('deploying canary (canary)')
             deployProcess = execSync('./deploy.sh canary dev');
             deployProcess.stdout.on('data', function(data){
               console.log(data);
             })
             deployProcess.stdout.on('exit', function(data){
               console.log('deploy exited with code'+code);
             })
          };
        }
        res.status(204).end()
     });
    
     pserver  = http.createServer(function(req, res) {
       count = count+1 % 10;
       if(prod_only == false && count % 10 == 5){
          console.log('proxy:Diverting 10% traffic to canary')
          client.get('canary',function(err, value){
            //console.log('redirecting to.. ');
            //console.log(value);
            proxy.web( req, res, {target: value })
          } );
       } else {
          if(prod_only == true)
          {
             //console.log('proxy:Diverting 100% traffic to production')
          }
          // route traffic across instances
          client.get('instances', function(err, value){
            var i; 
            i = count % value;
            pinstance = 'production'+ i.toString();
            client.get(pinstance,function(err, value){
                  console.log('Directing traffic to '+pinstance+' '+value);
                  proxy.web( req, res, {target: value })
             } );
          });
       }
     }).listen(3000);
     infra = app.listen(8000);
     
     var i;
     var wait=0;
     var autoscalling = setInterval(function(){
       rps = count/10;
       console.log('Request per second = '+rps);
       count = 0;
       if (rps > scale_limit && scale == 'down'){
          console.log('Scaling up')
          scale = 'busy'
          client.get('instances', function(err, value){
            i = parseInt(value,10);
            var inst = "production"+i.toString();
            var port = 3000+i
            var inst_port = port.toString() + ":3000"
            var content = ''
            content += fs.readFileSync("inventory_production",'utf8');
            content = content.replace("production","production"+i.toString());
            content = content.replace(/\n$/, '')
            content += " production_instance=production"+i.toString();
            content += " production_port="+inst_port
            fs.writeFileSync("inventory_scale"+i.toString(), content);
            var scaleProcess = execSync("ansible-playbook -i inventory_scale"+i.toString() +" scale_up.yml")
            scaleProcess.stdout.on('data', function(data){
                console.log(data);
            })
            scaleProcess.on('close', function(code, signal){
                client.get('production', function(err, value){
                 value = value.replace('3000','300'+i.toString());
                 client.set("production"+i.toString(),value);
                }); 
                var ins = parseInt(i, 10);
                //client.set("instances",ins+1);
                scale = 'ready'
                console.log("New instance is ready!");
            })
          });
       }
       else if(rps < scale_limit && scale == 'up'){
          console.log('Scaling Down')
          scale = 'busy'
          client.get('instances', function(err, value){
            i = parseInt(value,10)-1;
            var inst = "production"+i.toString();
            client.set("instances",i);
            var scaledownProcess = execSync("ansible-playbook -i inventory_scale"+i.toString() +" scale_down.yml")
            scaledownProcess.stdout.on('data', function(data){
                console.log(data);
            })
            scaledownProcess.on('close', function(code, signal){
               console.log("Scale down success!");
               scale = 'down';
            })
          });
       }
       else if (scale == 'ready'){
           wait++;
           if (wait > 2){
           wait = 0;
           var ins = parseInt(i, 10);
           client.set("instances",ins+1);
           scale = 'up'
           console.log('Scale Up success!');
           }
       }
     }, 10000);
  },

  teardown: function() {
     pserver.close();
     infra.close();
     //exec('./configure.py clean', function(){
     //    console.log("Infrastructure shutdown\n");
     // }
  },
}
infrastructure.setup();
// Clean Up
//process.on('exit', function(){infrastructure.teardown();} );
//process.on('SIGINT', function(){infrastructure.teardown();} );
//process.on('uncaughtException', function(err){
//  console.error(err);
//  infrastructure.teardown();} );
