BCI Art
========

Naoto Hieda (2016-2017) micuat@gmail.com

The current repository supports Python 3. For Python2.7, please checkout [eda1d498](https://github.com/micuat/bci_art/tree/eda1d4982ea2b48533537793c426c5bede3df207).

Instructions
--------

Install pip dependencies

    $ sudo pip install scikit-learn python-osc

Launch Muse-io

    $ muse-io --device Muse-XXXX --osc 'osc.udp://localhost:12000'

Launch Python SVM server

    $ python -u svm_server.py 12000 12100 13000 14000

Launch Node.js web server

    $ cd svm_control_nodejs
    $ npm install --save node-osc socket.io express serve-static
    $ node server.js 12100 13000 14000 3000


Bash Script
--------

    $ ./run.sh XXXX 12000 12100 13000 14000 3000
