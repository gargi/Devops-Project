#!/bin/bash
COUNTER=0
while [ $COUNTER -lt 70 ]; do
   let COUNTER=$COUNTER+1
   curl 52.32.39.187:3000
   echo ""
   sleep 0.5
done
