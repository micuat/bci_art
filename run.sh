#!/bin/bash

muse-io --device Muse-$1 --osc "osc.udp://localhost:$2" &
python2.7 svm_server.py $2 $3 &
cd svm_control_nodejs
node server.js $2 $3 $4