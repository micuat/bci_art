// $ node server.js 13000

var port_python = 12100;
var port_receive = 12200;
var port_of = process.argv[2];
var port_http = 3000;

var express = require('express');
var app = express();
var http = require('http').Server(app);
var io = require('socket.io')(http);

var osc = require('node-osc');
var svm_python = new osc.Client('127.0.0.1', port_python);
var of_client = new osc.Client('127.0.0.1', port_of);
var oscServer = new osc.Server(port_receive, '127.0.0.1');

oscServer.on("message", function (msg, rinfo) {
    console.log("message:");
    console.log(msg);
    io.emit('bci command', msg);
});

app.use('/', express.static('static'));

io.on('connection', function(socket){
    console.log('a user connected');
    socket.on('disconnect', function(){
        console.log('user disconnected');
    });
    socket.on('bci command', function(msg){
        io.emit('bci command', msg);
        svm_python.send(msg);
        console.log('message: ' + msg);
    });
    // socket.on('osc command', function(msg){
    //     console.log('message: ' + msg);
    //     of_client.send(msg.address, parseInt(msg.data));
    // });
});

http.listen(port_http, function(){
    console.log('listening on *:' + port_http);
});
