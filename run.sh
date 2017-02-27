#!/bin/bash

muse-io --device Muse-$1 --osc "osc.udp://localhost:$2" --osc-bp-urls 'osc.udp://localhost:'$5 &
python2.7 svm_server.py $2 $3 $4 &
cd svm_control_nodejs
node server.js $2 $3 $4 $5
