#!/bin/bash

# This script check if engine is running and restarts

if [[ "$#" -ne 2 ]]; then
   echo "Incorrect number of parameters! Syntax: ./check_engine.sh hostname atscale_install_dir"
   exit 3
fi

host=$1
atscaledir=$2 

atscaleCmd="http://$host:10502/ping"


curlCmd="curl -silent $atscaleCmd"

result=`eval $curlCmd`
case $result in 
    *OK*) echo "Engine Running OK";;
    *) echo "Will Restart engine"
       $atscaledir/bin/atscale_service_control restart engine;;
esac
