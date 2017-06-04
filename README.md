BCI Art
========

Naoto Hieda (2016) micuat@gmail.com

Instructions
--------

Install pip dependencies

    $ sudo pip install scikit-learn
    $ sudo pip install pyOSC --pre

Launch Muse-io

    $ muse-io --device Muse-XXXX --osc 'osc.udp://localhost:12000'

Launch Python SVM server

    $ python2.7 svm_server.py 12000 13000 14000

Launch Node.js web server

    $ cd svm_control_nodejs
    $ npm install --save node-osc socket.io express@4.10.2 serve-static
    $ node server.js 12000 13000 14000 3000


Bash Script
--------

    $ ./run.sh XXXX 12000 13000 14000 3000
